import logging
import json
import re
from typing import Any
from concurrent.futures import ThreadPoolExecutor

from pymongo import MongoClient, database

from bson.json_util import dumps, loads
from bson.objectid import ObjectId

from netpalm.backend.core.confload.confload import config, Config

import time

log = logging.getLogger(__name__)


class MongDB:
    def __init__(self):
        self.server = config.mongo_server_ip
        self.port = config.mongo_server_port
        self.username = config.mongo_user
        self.password = config.mongo_password

        if self.username:
            self.raw_connection = MongoClient(
                host=self.server,
                port=self.port,
                username=self.username,
                password=self.password,
            )
        else:
            self.raw_connection = MongoClient(
                host=self.server,
                port=self.port,
            )

        self.base_connection = self.raw_connection.netpalm

    def __ingress_parse_object_id(self, data: dict):
        if data.get("object_id", False):
            data["_id"] = ObjectId(data["object_id"])
            del data["object_id"]
        return data

    def __egress_parse_object_id(self, data: list):
        if len(data) >= 1:
            for idx, obj in enumerate(data, start=0):
                obj_id = obj["_id"]["$oid"]
                data[idx]["object_id"] = obj_id
                del data[idx]["_id"]
            return data

    def insert_one(self, collection, payload: dict):
        ret = self.base_connection[collection].insert_one(payload)
        return {"object_id": f"{ret.inserted_id}"}

    def insert_many(self, collection, payload: list):
        ret = self.base_connection[collection].insert_many(payload)
        resp_arr = []
        for obj in ret.inserted_ids:
            resp_arr.append({"object_id": f"{obj}"})
        return resp_arr

    def insert(self, data: Any, collection: str):
        """ wrapper for both insert_one and insert_many"""
        if isinstance(data, list):
            req_data = []
            for item in data:
                req_data.append(item)
            result = self.insert_many(collection=collection, payload=req_data)
        else:
            req_data = data
            result = self.insert_one(collection=collection, payload=req_data)
        return result

    def query(self, collection: str, payload: dict):
        """ wrapper for find with filtering """
        cleaned_data = self.__ingress_parse_object_id(payload)
        ret = self.base_connection[collection].find(cleaned_data)
        temp_json_result = dumps(ret)
        loaded_result = json.loads(temp_json_result)
        final_result = self.__egress_parse_object_id(loaded_result)
        if final_result is None or len(loaded_result) < 1:
            final_result = []
        return final_result

    def find(self, collection: str):
        ret = self.base_connection[collection].find()
        temp_json_result = dumps(ret)
        loaded_result = json.loads(temp_json_result)
        final_result = self.__egress_parse_object_id(loaded_result)
        if final_result is None:
            final_result = []
        return final_result

    def retrieve(self, query_obj: dict, object_id: str, collection: str):
        """ wrapper for both find and query"""
        if query_obj.get("filter", False):
            result = self.query(collection=collection, payload=query_obj["filter"])
        elif object_id:
            query_obj["filter"] = {}
            query_obj["filter"]["object_id"] = object_id
            result = self.query(collection=collection, payload=query_obj["filter"])
        elif object_id is None:
            result = self.find(collection=collection)
        return result

    def delete(self, query: dict, object_id: str, collection: str):
        final_result = []
        if query.get("filter", False):
            cleaned_data = self.__ingress_parse_object_id(query["filter"])
            ret = self.base_connection[collection].delete_many(cleaned_data)
            if ret.deleted_count >= 1:
                final_result = [{"deleted_object_count": ret.deleted_count}]
        if object_id:
            query["filter"] = {}
            query["filter"]["object_id"] = object_id
            cleaned_data = self.__ingress_parse_object_id(query["filter"])
            ret = self.base_connection[collection].delete_many(cleaned_data)
            if ret.deleted_count >= 1:
                final_result = [{"deleted_object_count": ret.deleted_count}]
        return final_result

    def update(self, data: dict, object_id: str, collection: str):
        final_result = []
        new_data = {"$set": data}
        query = {}
        query["filter"] = {}
        if object_id:
            query["filter"]["object_id"] = object_id
        cleaned_data = self.__ingress_parse_object_id(query["filter"])
        ret = self.base_connection[collection].update_many(cleaned_data, new_data)
        if ret.modified_count >= 1:
            final_result = [{"updated_object_count": ret.modified_count}]
        return final_result
