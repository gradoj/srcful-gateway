import json
from server.tasks.getNameTask import GetNameTask

from ..handler import GetHandler

from ..requestData import RequestData

class Handler(GetHandler):
  def doGet(self, request_data: RequestData):  
    
    return 200, json.dumps({'msek': request_data.bb.time_ms() - request_data.bb.startTime})