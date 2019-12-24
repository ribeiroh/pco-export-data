from people import people
from groups import groups
from maps import maps
import config
from geopy import distance
import json

##fetch full data from PCO in different places and build dictionaries indexed by ID
#build people data indexed by Id with marital statuses and addresses
peopleById = {}
temp_peopleList = people('').getAll()
temp_maritalStatuses = people('').getMaritalStatuses()

for maritalStatus in temp_maritalStatuses["data"]:
  temp_maritalStatuses[maritalStatus["id"]] = maritalStatus["attributes"]["value"]

for person in temp_peopleList["data"]:
  personId = person["id"]
  peopleById[personId] = person["attributes"]
  peopleById[personId].setdefault("addresses",[])
  try:
    peopleById[personId]["marital_status"] = temp_maritalStatuses[person["relationships"]["marital_status"]["data"]["id"]]
  except TypeError:
    peopleById[personId]["marital_status"] = None

for includedItem in temp_peopleList["included"]:
  if includedItem["type"] == "Address":
    peopleById[includedItem["relationships"]["person"]["data"]["id"]]["addresses"].append(includedItem["attributes"])

del temp_peopleList
del temp_maritalStatuses

#build a list of groups by Id
groupsById = {}
temp_groupsList = groups('').getAll()
for group in temp_groupsList["data"]:
  groupsById[group["id"]] = group["attributes"]
del temp_groupsList

#build a list groups for each person, and the location of each group
peopleToGroups = {}
locationsById = {}
temp_groupMembership = {} # this object is deleted once peopleToGroups is ready
for group in groupsById:
  groupObj = groups(group)
  groupObj.getDetails()
  #locationsById
  currentGroupLocation = groupObj.getLocation()
  if currentGroupLocation != None:
    locationsById[group] = currentGroupLocation["data"]
  else:
    locationsById[group] = None
  #temp_groupMembership
  currentGroupMembers = groupObj.getMembers()
  temp_groupMembership[group] = currentGroupMembers["data"]
for group, members in temp_groupMembership.items():
  for member in members:
    peopleToGroups.setdefault(str(member["attributes"]["account_center_identifier"]),[]).append(group)

#fill up with remaining people that do not belong to any groups
for person in peopleById:
  peopleToGroups.setdefault(person,[None])
del temp_groupMembership
## we're done building local dictionaries

testFile = open("test.json", "w+")
testFile.write(json.dumps(peopleById))
testFile.write(json.dumps(groupsById))
testFile.write(json.dumps(peopleToGroups))
testFile.write(json.dumps(locationsById))
#raise

outputFile = open("allMembersExport.csv", "w+")
# add new columns to csvHeader AND update the number of columns in csvPlaceholder
csvHeader = "First Name, Last Name, Gender, Birthdate, City, State, Zip, Location Long, Location Lat, Distance to Group, Marital Status, Membership, Status, Person Record Updated, Person Record Created, Joined Group At, Role, Group, Group Location, Group Long, Group Lat\r\n"
csvPlaceholder = ("\"%s\"," * 21) + "\r\n"
outputFile.write(csvHeader)

# go through every person in the list and output one line per group on the CSV file.
for person, groups in peopleToGroups.items():
  address = {}
  if len(peopleById[person]["addresses"]) > 0:
    for includedItem in peopleById[person]["addresses"]:
      if includedItem["primary"] == True:        
        address["city"] = includedItem["city"] if includedItem["city"] != None else ""
        address["state"] = includedItem["state"] if includedItem["state"] != None else ""
        address["zip"] = includedItem["zip"] if includedItem["zip"] != None else ""
        mapApi = maps(f"{address['city']} {address['state']} {address['zip']}")
        mapLocation = mapApi.getLocation()
  else:
    address["city"] = ""
    address["state"] = ""
    address["zip"] = ""
  for group in groups:
    if group is None:
      groupName = ""
      groupAddress = ""
      groupLong = ""
      groupLat = ""
    else:
      groupName = groupsById[group]["name"]
      if locationsById[group] != None:
        groupAddress = locationsById[group]["attributes"]["full_formatted_address"].replace("\n", ", ")
        groupLong = locationsById[group]["attributes"]["longitude"]
        groupLat = locationsById[group]["attributes"]["latitude"]
      else:
        groupAddress = ""
        groupLong = ""
        groupLat = ""
    if locationsById.get(group) != None:
      distanceUnit = config.UNIT if hasattr(config, 'UNIT') else 'miles'
      memberDistance = eval('distance.distance((groupLat, groupLong),(mapLocation["lat"], mapLocation["lng"])).' + distanceUnit)
    else:
      memberDistance = ""

    outputFile.write(csvPlaceholder % (
      peopleById[person]["first_name"],
      peopleById[person]["last_name"],
      peopleById[person]["gender"],
      peopleById[person]["birthdate"],
      address["city"],
      address["state"],
      address["zip"],
      mapLocation["lng"],
      mapLocation["lat"],
      memberDistance,
      peopleById[person]["marital_status"] if peopleById[person]["marital_status"] != None else '',
      peopleById[person]["membership"],
      peopleById[person]["status"],
      peopleById[person]["updated_at"],
      peopleById[person]["created_at"],
      
      member["attributes"]["joined_at"],
      member["attributes"]["role"],
      
      groupName,
      groupAddress,
      groupLong,
      groupLat
      ))
