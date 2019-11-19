from api import api

class people:
  peopleUrl = 'https://api.planningcenteronline.com/people/v2/people'
  peopleId = ''
  maritalUrl = ''
  martialStatusesUrl = 'https://api.planningcenteronline.com/people/v2/marital_statuses'
  addressUrl = ''

  def __init__(self, peepId):
    self.peopleId = peepId
  def getAll(self):
    return api().get('%s?include=addresses,marital_status&per_page=100' % (self.peopleUrl))
  def getPerson(self):
    resp = api().get('%s/%s' % (self.peopleUrl, self.peopleId))
    self.maritalUrl = resp["data"]["links"]["marital_status"]
    self.addressUrl = resp["data"]["links"]["addresses"]
    return resp
  def getMaritalStatus(self):
    if self.maritalUrl == None:
      return None
    else:
      return api().get(self.maritalUrl)
  def getMaritalStatuses(self):
    return api().get('%s?per_page=100' % (self.martialStatusesUrl))
  def getAddress(self):
    if self.addressUrl == None:
      return None
    else :
      return api().get(self.addressUrl)
