from asyncore import dispatcher
from email import message
from tkinter import EventType
from typing import Text, List, Any, Dict

from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.interfaces import Action
from rasa_sdk.events import SlotSet
import random
import pandas as pd
from word2number import w2n

path = "D:\Hotel Chatbot\data\hotel_data.csv" 
hotel_data = pd.read_csv(path)

class ValidateRoomForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_room_form"

    @staticmethod
    def room_type_db() -> List[Text]:
        list_room_type = list(hotel_data["room_type"])
        list_room_type = [i.lower() for i in list_room_type]
        return list_room_type
    
    def validate_room_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        room_type = (slot_value).lower()
        if room_type in ["one","one person","one people","1", "for one", "for 1"]:
            room_type = "single"
        elif room_type in ["two","two person","two people","2", "for two", "for 2"]:
            room_type = "double"
        elif room_type in ["three", "three person", "three people", "3", "for three", "for 3"]: 
            room_type = "triple"
        elif room_type in ["this", "that", "these", "those"]:
            room_type = tracker.get_slot("room_info")
        if room_type in self.room_type_db():
            # return {"room_type": room_type}
            quan = int(hotel_data.loc[hotel_data.room_type == str(room_type)].quantity)
            if quan:
                slot_quantity = tracker.get_slot("quantity")
                if slot_quantity in ["a" , "an"]:
                    slot_quantity = "1"
                room = self.quantity_db()   
                if not slot_quantity:
                    return {"quantity": None}
                if int(slot_quantity) <= room[room_type]:
                    return {"room_type": room_type,"quantity": slot_quantity}
                else:
                    dispatcher.utter_message(text= "There are too few available rooms")
                    return {"room_type": room_type,"quantity": None}                
                # return {"room_type": room_type}
            else: 
                dispatcher.utter_message(text = str(room_type) + " room is no more, Please choose another room type")
                return {"room_type": None}
        else:
            dispatcher.utter_message(text = "room type does not exist")
            return {"room_type" : None}
    
    def quantity_db(self):
        
        room_info = {}
        room_type = list(hotel_data.room_type)
        quantity = list(hotel_data.quantity)
        for i in range(len(room_type)):
            room_info[room_type[i]] = quantity[i]
        return room_info
    
    def validate_quantity(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        # hotel_data = pd.read_csv("E:D:\Hotel Chatbot\data\hotel_data.csv")
        slot_room_type = tracker.get_slot("room_type")
        if slot_value in ["a" , "an"]:
            slot_value = "1"
        slot_value = w2n.word_to_num(str(slot_value))
        
        if not slot_value:
            return {"quantity": None}
        room = self.quantity_db()     
        if int(slot_value) < 1: 
            dispatcher.utter_message(text="Invalid quantity")
            return {"quantity": None}
        if not slot_room_type:
            return {"quantity": slot_value}
        if int(slot_value) <= room[slot_room_type]:
            return {"quantity": slot_value}
        else:
            dispatcher.utter_message(text= "There are too few available rooms")
            return {"quantity": None}
    
    
class ValidateTimeAndIdForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_time_and_id_form"
    
    def id_card_db(self,s):
        result = ""
        for i in s: 
            if "0" <= i <= "9": 
                result += i
        return result 
                
    def validate_id_card(self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        slot_value = slot_value.lower()
        slot_value = slot_value.strip()
        slot_value = slot_value.replace("-"," ")
        slot_value = slot_value.split(' ')
        for i in range(len(slot_value)):
            try:
                if "A" <= slot_value[i][0] <= "z":
                    slot_value[i] = str(w2n.word_to_num(str(slot_value[i])))
            except:
                pass
        slot_value = "".join(slot_value)
        slot_value = slot_value.replace("and","")
        slot_value = self.id_card_db(slot_value)
        if len(slot_value) == 12:
            return {"id_card":slot_value}
        else: 
            dispatcher.utter_message(text = "ID card is not valid" )
            return {"id_card":None}
    
    def intend_time_db(self,time):
        time_split = time.split(" ")
        for i in range(len(time_split)):
            if time_split[i] == "tomorrow":
                time_split[i] = "1 day"
            try:
                time_split[i] = str(w2n.word_to_num(str(time_split[i])))
            except:
                pass
        return " ".join(time_split)
    
    def validate_intend_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        intend_time_slot = self.intend_time_db(slot_value)
        return {"intend_time": intend_time_slot}
        

class ActionResetData(Action):
    def name(self) -> Text:
        return "action_reset_data_rooms"
    
    def run(self, dispatcher,tracker,domain):
        global previous_room_info
        previous_room_info = None
        return [SlotSet("room_type", None),
                SlotSet("quantity", None),
                SlotSet("intend_time", None),
                SlotSet("reservation_form", None),
                SlotSet("room_info", None),
                SlotSet("check_room_rate", None)]
        
class ActionResetName(Action):
    def name(self) -> Text:
        return "action_reset_info_user"
    
    def run(self, dispatcher,tracker,domain):
        return [SlotSet("id_card", None),
                SlotSet("m_name", None)]
        
class ActionSaveReservationForm(Action):
    def name(self):
        return "action_save_reservation_form"
    
    def run(self, dispatcher,tracker,domain):
        intent = tracker.latest_message["intent"].get("name")
        if intent == "book_room_now" :
            return [SlotSet("reservation_form", "now")]        
        if intent == "book_in_advance" :
            return [SlotSet("reservation_form", "reservation")]   
        return []

class ActionSaveData(Action):
    def name(self):
        return "action_save_data"
    
    def run(self, dispatcher,tracker,domain):
        room_type_slot = (tracker.get_slot("room_type"))
        quantity_slot = tracker.get_slot("quantity")
        intend_time_slot = (tracker.get_slot("intend_time"))
        name_slot = (tracker.get_slot("m_name"))
        reservation_form_slot = (tracker.get_slot("reservation_form"))
        id_card_slot = tracker.get_slot("id_card")
        
        info = pd.read_csv("D:\Hotel Chatbot\data\data_reservation.csv")
        
        list_index = list(info.index)
        count = 0
        if len(list_index) == 0:
            count = 1
        else:
            count = list_index[-1] 
        row_info = pd.DataFrame([[name_slot,id_card_slot,room_type_slot,quantity_slot,intend_time_slot,reservation_form_slot]], 
                                columns= "name,id_card,room_type,quantity,intend_time,reservation_form".split(",") , index = [count+1])
        info = pd.concat([info,row_info])
        info.to_csv("D:\Hotel Chatbot\data\data_reservation.csv", index = False)
        dispatcher.utter_message("Save user data successfully")
        return []




class ActionChangeDataHotel(Action):
    def name(self):
        return "action_change_data_hotel"       
    
    def run(self, dispatcher,tracker,domain):
        
        # hotel_data = pd.read_csv("E:D:\Hotel Chatbot\data\hotel_data.csv")
        quantity_slot = int(tracker.get_slot("quantity"))
        room_type_slot = (tracker.get_slot("room_type")).lower()
        row = list(hotel_data.loc[hotel_data.room_type == str(room_type_slot)].index)[0]
        quantity_change = str(int(hotel_data["quantity"].iloc[row]) - int(quantity_slot))
        hotel_data["quantity"].iloc[row] = quantity_change
        hotel_data.to_csv("D:\Hotel Chatbot\data\hotel_data.csv",index = False)
        return []
        
# class ActionCheckChangeRoom(Action):
#     def name(self):
#         return "action_check_change_room_type"
    
#     def run(self, dispatcher,tracker,domain):
#         change_room_type = tracker.get_slot("change_room_type")
#         if not change_room_type:
#             dispatcher.utter_message(text="What type of room do you want to change to?")
#             return [SlotSet("check_change_room", False)]
#         else: 
#             return [SlotSet("check_change_room", True)]
        
class ValidateChangeRoomForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_change_room_form"

    @staticmethod
    def room_type_db() -> List[Text]:
        """Database of supported"""
        list_room_type = list(hotel_data["room_type"])
        list_room_type = [i.lower() for i in list_room_type]
        return list_room_type
    
    def validate_change_room_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        room_type = (slot_value).lower()
        quan = int(hotel_data.loc[hotel_data.room_type == str(room_type)].quantity)

        if slot_value.lower() in self.room_type_db():
            if quan :
                return {"change_room_type": slot_value.lower()}
            else: 
                dispatcher.utter_message(text = str(room_type) + " room is no more, Please choose another room type")
                return {"change_room_type": None}
        else:
            dispatcher.utter_message(text = "Room type does not exist")
            return {"change_room_type": None}
        
        
class ActionResetChangeRoom(Action):
    def name(self):
        return "action_reset_change_room"
    
    def run(self, dispatcher,tracker,domain):
        intent = tracker.latest_message["intent"].get("name")
        change_room_type = tracker.get_slot("change_room_type")
        # if intent == "confirm":
        #     dispatcher.utter_message(text = "Successful room change")
        #     return [SlotSet("room_type" , change_room_type) , SlotSet("change_room_type" , None)]
        # else: 
        #     dispatcher.utter_message(text = "The hotel booking is cancelled")
        #     return [SlotSet("change_room_type" , None)]
        dispatcher.utter_message(text = "Successful room change")
        return [SlotSet("room_type" , change_room_type) , SlotSet("change_room_type" , None)]
    
    
# class ValidateIntendTimeForm(FormValidationAction):
#     def name(self) -> Text:
#         return "validate_intend_time_form"

#     @staticmethod
#     def intend_time_db(time):
#         time_split = time.split(" ")
#         for i in range(len(time_split)):
#             if time_split[i] == "tomorrow":
#                 time_split[i] = "1"
#             try:
#                 time_split[i] = str(w2n.word_to_num(time_split[i]))
#             except:
#                 pass
#         return " ".join(time_split)
    
#     def validate_intend_time(
#         self,
#         slot_value: Any,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: DomainDict,
#     ) -> Dict[Text, Any]:

#         intend_time_slot = self.intend_time_db(slot_value)
#         return {"intend_time": intend_time_slot}
    
    
    
class CheckRoomRate(Action):
    def name(self) -> Text:
        return "action_inform_room_rate"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # hotel_data = pd.read_csv("E:\hotel_chatbot\data\hotel_data.csv")
        slot_room_type = tracker.get_slot("room_info")
        index_room_type = (hotel_data.loc[hotel_data.room_type == slot_room_type].index)[0]
        room_rate = list(hotel_data["room_rate"])[index_room_type]
        dispatcher.utter_message(text = "The " + slot_room_type + " room price " + room_rate +"/day")
        utter = ["Would you book this room type?","Would you like to book this room type ?"]
        global pre_action_room_info
        pre_action_room_info = "action_inform_room_rate"
        # dispatcher.utter_message(text = random.choice(utter))
        return []

global previous_room_info 
previous_room_info = None

class ValidateRoomInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_room_info_form"

    @staticmethod
    def room_type_db() -> List[Text]:
        list_room_type = list(hotel_data["room_type"])
        list_room_type = [i.lower() for i in list_room_type]
        return list_room_type
    
    def validate_room_info(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        
        room_type = slot_value
        global previous_room_info
        if room_type in ["this" , "that"]:
            if not (tracker.get_slot("room_type")):
                room_type = previous_room_info
            else: 
                room_type = tracker.get_slot("room_type")
        if room_type in self.room_type_db():
            quan = int(hotel_data.loc[hotel_data.room_type == str(room_type)].quantity)
            if quan:
                previous_room_info = room_type.lower()
                return {"room_info": room_type.lower()}
            else: 
                dispatcher.utter_message(text = str(room_type) + " room is no more, Please choose another room type")
                return {"room_info": None}
        else:
            dispatcher.utter_message(text = "Room type does not exist")
            return {"room_info" : None}
    
class ActionCheckQuantityRoom(Action):
    def name(self) -> Text:
        return "action_inform_quantity_available"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # hotel_data = pd.read_csv("E:\hotel_chatbot\data\hotel_data.csv")

        room_type = tracker.get_slot("room_info")
        
        quan = int(hotel_data.loc[hotel_data.room_type == str(room_type)].quantity)

        dispatcher.utter_message(text = "My hotel has " + str(quan) + " " + str(room_type) +" rooms available")
        utter = ["Would you book this room type?","Would you like to book this room type ?"]
        
        global pre_action_room_info
        pre_action_room_info = "action_inform_quantity_available"
        
        # dispatcher.utter_message(text = random.choice(utter))
        return []
    
class ActionResetChangeRoom(Action):
    def name(self):
        return "action_reset_room_info"
    
    def run(self, dispatcher: CollectingDispatcher,tracker,domain):
        intent = tracker.latest_message["intent"].get("name")
        room_info = tracker.get_slot("room_info")
        
        if intent == "booking_this_room":
            return [SlotSet("room_type" , room_info) , SlotSet("room_info" , None)]
        else: 
            return [SlotSet("room_info" , None)]
        
class ActionInformNumberRoomType(Action):
    def name(self):
        return "action_faq_ask_number_room_type"
    
    def run(self, dispatcher: CollectingDispatcher,tracker,domain):
        room_type = list(hotel_data.room_type)
        num = len(room_type)
        room_type = ", ".join(room_type)
        text1 = "Currently our hotel has " + str(num) + " types of rooms: " + room_type
        text2 = "It includes " + str(num) + " kinds of rooms: " + room_type
        utter = []
        utter.append(text1)
        utter.append(text2)
        dispatcher.utter_message(text = random.choice(utter))
        return []
    
global pre_action_room_info 
pre_action_room_info = None

class ActionCheckPreviousQuestion(Action):
    def name(self):
        return "action_check_pre_question"
    
    def run(self, dispatcher: CollectingDispatcher,tracker,domain):
        global pre_action_room_info
        if pre_action_room_info == "action_inform_quantity_available":
            return [SlotSet("check_room_rate", False)]
        else:
            return [SlotSet("check_room_rate", True)]


date_picker = {
    "blocks": [
        {
            "type": "section",
            "text":{
                "text": "Make a bet on when the world will end:",
                "type": "mrkdwn"
      },
      "accessory":
      {
        "type": "datepicker",
        "initial_date": "2019-05-21",
        "placeholder":
        {
          "type": "plain_text",
          "text": "Select a date"
        }
      }
    }
  ]
}
class ActionCheckDatePicker(Action):
    def name(self) -> Text:
        return "action_check_date_picker"
    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        dispatcher.utter_message(json_message = date_picker)