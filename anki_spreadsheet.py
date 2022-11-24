from re import L
import requests
import pandas as pd
import datetime
import json

SPREADSHEET_PATH = "/home/anon/Documents/sentence_bank2.csv"
ANKI_CONNECT_API = "http://192.168.1.201:8765" #Windows box
DECK_NAME = "Sentence Mining"
DECK_MODEL = "Japanese (recognition)-9536e"

def addNote(deck_name, model_name, note_front, note_back):
    params = {
        "note": {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": {
                "Expression": note_front,
                "Meaning": note_back,
                "Reading": ""
            }
        }
    }
    req = {
        "action": "addNote",
        "version": 6,
        "params": params
    }
    try:
        response = json.loads(requests.post(ANKI_CONNECT_API,json=req).content)
        if(response['result']):
            print("New card")
            print("Front: ", note_front)
            print("Back: ", note_back)
            print('Created card')
        elif(response['error']):
            raise Exception(response['error'])
    except Exception as err:
        print(f"Error: {err}")
    else:
        print("Success")

def getDeckStats(decks):
    req = {
        "action": "getDeckStats",
        "version": 6,
        "params": { 
            "decks": decks
        }
    }
    try:
        response = json.loads(requests.post(ANKI_CONNECT_API,json=req).content)
        if(response['result']):
            return response['result']
        elif(response['error']):
            raise Exception(response['error'])
    except Exception as err:
        print(f"Error: {err}")

def getDeckNamesAndIds():
    req = {
        "action": "deckNamesAndIds",
        "version": 6,
    }
    try:
        response = json.loads(requests.post(ANKI_CONNECT_API,json=req).content)
        if(response['result']):
            return response['result']
        elif(response['error']):
            raise Exception(response['error'])
    except Exception as err:
        print(f"Error: {err}")

def ankiSync():
    req = {
        "action": "sync",
        "version": 6,
    }
    try:
        response = json.loads(requests.post(ANKI_CONNECT_API,json=req).content)
        if(response['result']):
            return response['result']
        elif(response['error']):
            raise Exception(response['error'])
    except Exception as err:
        print(f"Error: {err}")

sheet_df = pd.read_csv(SPREADSHEET_PATH)
print(sheet_df.dtypes)
print(getDeckNamesAndIds())
deck_id = str(getDeckNamesAndIds()[DECK_NAME])
print(DECK_NAME, ", id: ", deck_id)
stats = getDeckStats(decks=[DECK_NAME])[deck_id]
print("Current card count: ", stats['total_in_deck'])
ctr = 0;

for index, row in sheet_df.iterrows():
    if(pd.isna(row['j-definition-card-created'])):
        #make monolingual card first
        if not pd.isna(row['sentence']) and not pd.isna(row['j-definition']):
            print("Create monolingual card")
            addNote(DECK_NAME, DECK_MODEL, row['sentence'],row['j-definition']);
            sheet_df.loc[index, 'j-definition-card-created'] = datetime.datetime.now();
            sheet_df.loc[index, 'total-needed'] = stats['total_in_deck'] + ctr + 10;
            ctr = ctr + 1
    else:
        #make bilingual definition card if 10 new cards have been created since the monlingual card was created
        if(pd.isna(row['e-definition-card-created'])):
            if not pd.isna(row['j-definition']) and not pd.isna(row['e-definition']):
                if(stats['total_in_deck'] >= sheet_df.loc[index, 'total-needed']):
                    sheet_df.loc[index, 'e-definition-card-created'] = datetime.datetime.now();
                    print("Create bilingual card")
                    addNote(DECK_NAME, DECK_MODEL, row['j-definition'],row['e-definition']);

print('Syncing with Anki')
ankiSync()
sheet_df.to_csv(SPREADSHEET_PATH, index=False)
