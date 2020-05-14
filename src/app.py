import config
import torch
import flask
from flask import Flask, request
from model import BERTBaseUncased

app = Flask(__name__)

DEVICE = "cuda"


def sentence_prediction(sentence, model):
    tokenizer = config.TOKENIZER
    max_length = config.MAX_LEN
    review = str(sentence)
    review = ' '.join(review.split())
    inputs = tokenizer.encode_plus(
        review,
        pad_to_max_length=True,
        max_length=max_length
    )
    ids = inputs["input_ids"]
    mask = inputs["attention_mask"]
    token_type_ids = inputs["token_type_ids"]

    padding_length = max_length - len(ids)
    ids = ids + ([0] * padding_length)
    mask = mask + ([0] * padding_length)
    token_type_ids = token_type_ids + ([0] * padding_length)

    ids = torch.tensor(ids, dtype=torch.long).unsqueeze(0)
    mask = torch.tensor(mask, dtype=torch.long).unsqueeze(0)
    token_type_ids = torch.tensor(token_type_ids, dtype=torch.long).unsqueeze(0)

    ids = ids.to(DEVICE, dtype=torch.long)
    mask = mask.to(DEVICE, dtype=torch.long)
    token_type_ids = token_type_ids.to(DEVICE, dtype=torch.long)

    outputs = model(
        ids=ids,
        mask=mask,
        token_type_ids=token_type_ids
    )
    outputs = torch.sigmoid(outputs).cpu().detach().numpy()
    return outputs[0][0]


@app.route("/predict")
def predict():
    sentence = request.args.get("sentence")
    positive_prediction = sentence_prediction(sentence, model=MODEL)
    negative_prediction = 1 - positive_prediction
    response = {}
    response["response"] = {
        'positive': str(positive_prediction),
        'negative': str(negative_prediction),
        'sentence': str(sentence)
    }
    return flask.jsonify(response)


if __name__ == '__main__':
    MODEL = BERTBaseUncased()
    MODEL.to(DEVICE)
    MODEL.eval()
    app.run(host='0.0.0.0')