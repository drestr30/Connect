import json
import traceback
import azure.functions as func
# from requests import options
import db_operations as db
import llm_operations as llm
from utils import generate_hash_str
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)
        

@app.route(route="create_session", methods=["POST"])
def create_session(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        selections = req_body.get('selections')
        selections['dynamic'] = selections['dynamic'].lower()
        selection_name = "-".join([k if isinstance(v, bool) and v else str(v)
                                for k, v in selections.items()
                                if (isinstance(v, str)) or (isinstance(v, bool) and v)])
        
        selection_hash = generate_hash_str(selection_name)
        logging.info(f"Received selections: {selection_name} with selections {selections}")
        session_id = db.start_session(selections, selection_name, selection_hash)
        sys, user =  llm.format_prompt_templates(selections)
        logging.info(f"Started session with ID: {session_id}")

        return func.HttpResponse(json.dumps({"session_id": session_id, 
                                             "system_message": sys,
                                             "user_message": user}), 
                                 status_code=200, 
                                 mimetype="application/json")  
    
    return func.HttpResponse(
         "This HTTP triggered function executed successfully. Pass selections in the request body for a personalized response.",
         status_code=200
    )

@app.route(route="get_cards/{session_id}", methods=["GET"])
def get_cards(req: func.HttpRequest) -> func.HttpResponse:
    """         """
    logging.info('Python HTTP trigger function processed a request.')
    SAMPLE_SIZE = 10
    LIFETIME_POLICY = 5  # max times a card can be shown before being retired
    session_id = req.route_params.get('session_id')

    if not session_id:
        return func.HttpResponse(
            "Please provide a session_id.",
            status_code=400
        )
    else:

        try:
            session_info = db.get_session(session_id)
            logging.info(f"Retrieved session info: {session_info['selection_name']}")
            available_cards = db.get_cards_by_hash(session_info['selection_hash'], policy=LIFETIME_POLICY)
            logging.info(f"Retrieved session cards with {len(available_cards)} cards")

            if len(available_cards) < SAMPLE_SIZE:
                logging.info("Not enough cards found, generating new cards...")
                generated_cards = llm.generate_session_cards(session_info['selection'])
                new_cards = [card['description'] for card in generated_cards]
                card_ids = db.create_cards(new_cards, session_info['selection_hash'], session_info['selection_name'])
                for card_id in card_ids:
                    logging.info(f"Created new card with ID: {card_id}")
            # else: 
            session_cards = db.sample_cards_by_hash(session_info['selection_hash'], 
                                                    sample_size=SAMPLE_SIZE,
                                                    policy=LIFETIME_POLICY)
            
            db.create_session_cards(session_id, 
                                    [card['id'] for card in session_cards],)
            
            return func.HttpResponse(json.dumps(session_cards), 
                                        status_code=200, 
                                        mimetype="application/json")
        except Exception as e:
            logging.error(f"Error retrieving or generating cards: {e}")
            logging.error(traceback.format_exc())
            return func.HttpResponse(
                f"Error processing request: {e}",
                status_code=500
            )
        
@app.route(route="update_card_status", methods=["POST"])
def update_card_status(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
    except ValueError:
        pass
    else:
        session_id = req_body.get('session_id', None)
        card_id = req_body.get('card_id')
        liked = req_body.get('liked', None)
        disliked = req_body.get('disliked', None)

        if not card_id:
            return func.HttpResponse(
                "Please provide card_id.",
                status_code=400
            )

        db.update_card_status(card_id, liked=liked)
        db.update_session_card(session_id, card_id)

        return func.HttpResponse(
            json.dumps({"status": "success"}),
            status_code=200,
            mimetype="application/json"
        )

    return func.HttpResponse(
        "This HTTP triggered function executed successfully. Pass session_id and card_id in the request body for a personalized response.",
        status_code=200
    )

@app.route(route="get_dynamics", methods=["GET"])
def get_dynamics(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Get dynamics endpoint hit.')

    dynamics = db.get_dynamics()
    logging.info(f"Retrieved dynamics: {dynamics}")

    return func.HttpResponse(
        json.dumps(dynamics),
        status_code=200,
        mimetype="application/json"
    )
