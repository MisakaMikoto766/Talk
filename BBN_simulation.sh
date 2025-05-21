set -e
set -u

# MAD_PATH=$(realpath `dirname $0`)
MAD_PATH=BBN

python3 $MAD_PATH/code/doc_pat_int.py \
    -i $MAD_PATH/data/BBN/data/dxy/dxy_with_traits.json \
    -o $MAD_PATH/data/BBN/output/dxy/ \
    -m your_model_name \
    -k  your_api_key \
