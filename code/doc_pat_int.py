
import os
import json
import random
# random.seed(0)
import argparse
from langcodes import Language
from utils.agent_url import Agent
from datetime import datetime
from tqdm import tqdm
from utils.extract_tools import extract_patient_condition, extract_preknow_condition, extract_bigfive_traits, extract_bigfive_scores, extract_education_category, extract_simulated_behaviors


NAME_LIST=[
    "Doctor",
    "Patient",
    "Moderator",
]


class BBNPlayer(Agent):
    def __init__(self, model_name: str, name: str, temperature:float, openai_api_key: str, sleep_time: float) -> None:
        """Create a player in the BBN

        Args:
            model_name(str): model name
            name (str): name of this player
            temperature (float): higher values make the output more random, while lower values make it more focused and deterministic
            openai_api_key (str): As the parameter name suggests
            sleep_time (float): sleep because of rate limits
        """
        super(BBNPlayer, self).__init__(model_name, name, temperature, openai_api_key, sleep_time)
        self.openai_api_key = openai_api_key
        self.model_name = model_name


class BBN:
    def __init__(self,
            model_name: str=None, 
            temperature: float=0.7, 
            num_players: int=3, 
            save_file_dir: str=None,
            openai_api_key: str=None,
            prompts_path: str=None,
            max_round: int=10,                    
            sleep_time: float=0
        ) -> None:
        """Create a BBN

        Args:
            model_name (str): openai model name
            temperature (float): higher values make the output more random, while lower values make it more focused and deterministic
            num_players (int): num of players
            save_file_dir (str): dir path to json file
            openai_api_key (str): As the parameter name suggests
            prompts_path (str): prompts path (json file)
            max_round (int): maximum Rounds of BBN
            sleep_time (float): sleep because of rate limits
        """

        self.model_name = model_name
        self.temperature = temperature
        self.num_players = num_players
        self.save_file_dir = save_file_dir
        self.openai_api_key = openai_api_key
        self.max_round = max_round
        self.sleep_time = sleep_time

        # init save file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H:%M:%S")

        self.save_file = {
            'start_time': current_time,
            'end_time': '',
            'model_name': model_name,
            'temperature': temperature,
            'num_players': num_players,
            'success': False,
            "patient_condition": "",
            "preknow_condition": "",
            "Summary of Informing Situation": '',
            "Reason": '',
            'players': {},
            'dialog_history': "",
            'personality': "",
            'personality_score': "",
            'edu_category': "",
            'edu_behavior': "",
            'rounds_completed': 0,
        }
        prompts = json.load(open(prompts_path))
        self.save_file.update(prompts)
        self.init_prompt()

        # creat&init agents
        self.creat_agents()
        self.init_agents()
    
    def init_prompt(self):
        def prompt_replace(key):
            self.save_file[key] = self.save_file[key].replace("##patient_condition##", self.save_file["patient_condition"]).replace("##preknow_condition##", self.save_file["preknow_condition"])
        prompt_replace("doctor_system_prompt")
        prompt_replace("patient_system_prompt")
        prompt_replace("moderator_system_prompt")


    def creat_agents(self):
        # creates players
        self.players = [
            BBNPlayer(model_name=self.model_name, name=name, temperature=self.temperature, openai_api_key=self.openai_api_key, sleep_time=self.sleep_time) for name in NAME_LIST
        ]
        self.doctor = self.players[0]
        self.patient = self.players[1]
        self.moderator = self.players[2]

    def init_agents(self):
        self.doctor.set_meta_prompt(self.save_file['doctor_system_prompt'])
        self.patient.set_meta_prompt(self.save_file['patient_system_prompt'].replace('##personality_trait##', self.save_file["personality"]).replace('##education##', self.save_file["edu_behavior"]))


        print(f"===== Converstaion Round-1 =====\n")
        self.doctor.add_event(self.save_file['doctor_init_prompt'])
        self.doc_ans = self.doctor.ask()
        self.doctor.add_memory(self.doc_ans)

        self.patient.add_event(self.save_file['patient_init_prompt'].replace('##doctor response##', self.doc_ans))
        self.pat_ans = self.patient.ask()
        self.patient.add_memory(self.pat_ans)

        self.update_dialog_history("Round-1", self.doc_ans, self.pat_ans)

        self.moderator.add_event(self.save_file['moderator_prompt'].replace('##dialog_history##', self.save_file['dialog_history']).replace('##patient_condition##', self.save_file["patient_condition"]))
        self.mod_ans = self.moderator.ask()
        self.moderator.add_memory(self.mod_ans)

        self.mod_ans = self.mod_ans.replace('```json', '').replace('```', '').strip()
        self.mod_ans = json.loads(self.mod_ans)


    def update_dialog_history(self, round_name, doc_ans, pat_ans):
        round_history = f"===== {round_name} =====\ndoctor：{doc_ans}\npatient：{pat_ans}\n"
        self.save_file['dialog_history'] += round_history

    def update_doctor_history(self, round_name, doc_ans):
        round_history = f"===== {round_name} =====\ndoctor：{doc_ans}\n"
        self.save_file['dialog_history'] += round_history
    def update_patient_history(self, round_name, pat_ans):
        round_history = f"patient：{pat_ans}\n"
        self.save_file['dialog_history'] += round_history

    def round_dct(self, num: int):
        dct = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth',
            5: 'fifth', 6: 'sixth', 7: 'seventh', 8: 'eighth',
            9: 'ninth', 10: 'tenth'
        }
        return dct.get(num, f'round-{num}')


    def save_file_to_json(self, id):
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H:%M:%S")
        save_file_path = os.path.join(self.save_file_dir, f"{id}.json")
        for key in ["patient_condition", "preknow_condition", "players"]:
            if key in self.save_file:
                del self.save_file[key]

        self.save_file['end_time'] = current_time
        json_str = json.dumps(self.save_file, ensure_ascii=False, indent=4)
        with open(save_file_path, 'w') as f:
            f.write(json_str)

    
    def broadcast(self, msg: str):
        """Broadcast a message to all players. 
        Typical use is for the host to announce public information

        Args:
            msg (str): the message
        """
        # print(msg)
        for player in self.players:
            player.add_event(msg)
    def speak(self, speaker: str, msg: str):
        """The speaker broadcast a message to all other players. 

        Args:
            speaker (str): name of the speaker
            msg (str): the message
        """
        if not msg.startswith(f"{speaker}: "):
            msg = f"{speaker}: {msg}"
        # print(msg)
        for player in self.players:
            if player.name != speaker:
                player.add_event(msg)

    def ask_and_speak(self, player: BBNPlayer):
        ans = player.ask()
        player.add_memory(ans)
        self.speak(player.name, ans)



    def run(self):

        for round in range(self.max_round - 1):
            if self.mod_ans["Summary of Informing Situation"] != '':
                break
            else:
                print(f"===== Conversation Round-{round+2} =====\n")
                doctor_prompt = self.save_file['doctor_prompt'] \
                    .replace('##dialog_history##', self.save_file['dialog_history'])\
                    .replace('##round##', self.round_dct(round+2)) \
                    .replace('##resround##', self.round_dct(self.max_round-(round+2)))

                self.doc_ans = self.doctor.ask_single_turn(doctor_prompt)
                self.doctor.add_memory(self.doc_ans)
                self.update_doctor_history(f"Round-{round+2}", self.doc_ans)

                patient_prompt = self.save_file['patient_prompt'].replace('##dialog_history##', self.save_file['dialog_history'])
                self.pat_ans = self.patient.ask_single_turn(patient_prompt)
                self.patient.add_memory(self.pat_ans)

                self.update_patient_history(f"Round-{round+2}", self.pat_ans)

                moderator_prompt = self.save_file['moderator_prompt'].replace('##dialog_history##', self.save_file['dialog_history']).replace('##round##', self.round_dct(round+2)).replace('##patient_condition##', self.save_file["patient_condition"])
                self.mod_ans = self.moderator.ask_single_turn(moderator_prompt)
                self.moderator.add_memory(self.mod_ans)
                self.mod_ans = self.mod_ans.replace('```json', '').replace('```', '').strip()
                self.mod_ans = json.loads(self.mod_ans)

        
        if self.mod_ans["Summary of Informing Situation"] != '':
            self.save_file.update(self.mod_ans)
            self.save_file['success'] = True

        else:
            self.save_file["Reason"] = self.mod_ans["Reason"]
            self.save_file["success"] = False

        for player in self.players:
            self.save_file['players'][player.name] = player.memory_lst
        
        self.save_file['rounds_completed'] = round + 1

def parse_args():
    parser = argparse.ArgumentParser("", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input-file", type=str, required=True, help="Input file path")
    parser.add_argument("-o", "--output-dir", type=str, required=True, help="Output file dir")
    parser.add_argument("-k", "--api-key", type=str, required=True, help="OpenAI api key")
    parser.add_argument("-m", "--model-name", type=str, default="gpt-4o", help="Model name")
    parser.add_argument("-t", "--temperature", type=float, default=0, help="Sampling temperature")

    return parser.parse_args()
    

if __name__ == "__main__":
    args = parse_args()
    openai_api_key = args.api_key
    model_name = args.model_name

    current_script_path = os.path.abspath(__file__)
    MAD_path = current_script_path.rsplit("/", 2)[0]

    config = json.load(open(f"{MAD_path}/code/utils/config_name.json", "r"))

    with open(args.input_file, "r") as f:
        inputs = json.load(f)

    save_file_dir = args.output_dir
    if not os.path.exists(save_file_dir):
        os.mkdir(save_file_dir)

    for id, data in enumerate(tqdm(inputs)):
        patient_condition = extract_patient_condition(data)
        preknow_condition = extract_preknow_condition(data)
        personality = extract_bigfive_traits(data)
        personality_score = extract_bigfive_scores(data)
        edu_category = extract_education_category(data)
        edu_behavior = extract_simulated_behaviors(data)

        prompts_path = f"{save_file_dir}/{id}-config.json"

        config['personality'] = personality
        config['personality_score'] = personality_score
        config['edu_category'] = edu_category
        config['edu_behavior'] = edu_behavior


        


        with open(prompts_path, "w") as file:
            json.dump(config, file, ensure_ascii=False, indent=4)

        try:
            bbn = BBN(save_file_dir=save_file_dir, num_players=3, model_name=model_name,
                    openai_api_key=openai_api_key, prompts_path=prompts_path,
                    temperature=0, sleep_time=0)
            bbn.run()
        except Exception as e:
            bbn = BBN(save_file_dir=save_file_dir, num_players=3, model_name=model_name,
                    openai_api_key=openai_api_key, prompts_path=prompts_path,
                    temperature=0, sleep_time=0)
            bbn.save_file['success?'] = False
            bbn.save_file['Reason?'] = str(e)
        finally:
            bbn.save_file_to_json(id)

            try:
                with open(prompts_path, "r", encoding="utf-8") as f:
                    current_config = json.load(f)

                current_config['rounds_completed'] = bbn.save_file.get('rounds_completed', 0)

                with open(prompts_path, "w", encoding="utf-8") as f:
                    json.dump(current_config, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"[WARN] Failed to update rounds_completed in config for ID {id}: {e}")