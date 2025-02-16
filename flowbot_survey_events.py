from datetime import datetime
import math
from typing import Dict
import sqlite3
from flowbot_database import Tables
# from contextlib import closing

class surveyEvent():

    eventName = ''
    eventType = 'Unknown'
    eventStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
    eventEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def __init__(self):
        self.eventName = ''
        self.eventType = 'Unknown'
        self.eventStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.eventEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def from_database_row(self, row):
        self.eventName = row[0]
        self.eventType = row[1]
        self.eventStart = datetime.fromisoformat(row[2])
        self.eventEnd = datetime.fromisoformat(row[3])

    def duration(self):
        return self.eventEnd - self.eventStart

    def durationFormattedString(self):
        duration_seconds = (self.eventEnd - self.eventStart).total_seconds()
        hours = math.floor(duration_seconds / 3600)
        minutes = math.floor((duration_seconds / 60) % 60)
        return f'{hours}hr {minutes}min'

    # def durationFormattedString(self):
    #     return f'{math.floor(((self.eventEnd - self.eventStart).total_seconds() / 60.0) / 60)}hr
    # {math.floor((self.eventEnd - self.eventStart).total_seconds() / 60.0) -
    # (math.floor(((self.eventEnd - self.eventStart).total_seconds() / 60.0) / 60) * 60)}min'


class surveyEvents():

    # survEvents: Dict[str, surveyEvent]
    # __seEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
    # __seLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def __init__(self):
        self.survEvents: Dict[str, surveyEvent] = {}
        self.__seEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.__seLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def read_from_database(self, conn: sqlite3.Connection):
        c = conn.cursor()
        try:
            c.execute(f"SELECT * FROM {Tables.SURVEY_EVENT}")
        except sqlite3.OperationalError as e:
            print(f"Table '{Tables.SURVEY_EVENT}' does not exist.")
            return  # Return without attempting to fetch rows
        
        rows = c.fetchall()
        for row in rows:
            event = surveyEvent()
            event.from_database_row(row)
            self.survEvents[event.eventName] = event

    def write_to_database(self, conn: sqlite3.Connection) -> bool:

        result = False
        try:

            conn.execute(f'''CREATE TABLE IF NOT EXISTS {Tables.SURVEY_EVENT} (
                            eventName TEXT PRIMARY KEY,
                            eventType TEXT,
                            eventStart TEXT,
                            eventEnd TEXT
                        )''')
            for event in self.survEvents.values():
                conn.execute(f'''INSERT OR REPLACE INTO {Tables.SURVEY_EVENT} VALUES (?, ?, ?, ?)''',
                        (event.eventName, event.eventType, event.eventStart.isoformat(), event.eventEnd.isoformat()))
            conn.commit()
            result = True

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
        except Exception as e:
            print(f"Exception in _query: {e}")
            conn.rollback()
        finally:
            return result
        #     conn.close()

    def getEaliestStart(self):
        return self.__seEarliestStart

    def getLatestEnd(self):
        return self.__seLatestEnd

    def setEaliestStart(self, startDate):
        self.__seEarliestStart = startDate

    def setLatestEnd(self, endDate):
        self.__seLatestEnd = endDate

    def clear(self):
        self.survEvents.clear()
        self.updateMinMaxValues()

    def addSurvEvent(self, objSE):

        if objSE.eventName not in self.survEvents:

            self.survEvents[objSE.eventName] = objSE
            self.updateMinMaxValues()

            return True

        else:

            return False

    def getSurveyEvent(self, nameSE):

        if nameSE in self.survEvents:
            return self.survEvents[nameSE]

    def removeSurveyEvent(self, nameSE):

        if nameSE in self.survEvents:
            self.survEvents.pop(nameSE)
            self.updateMinMaxValues()

    def updateMinMaxValues(self):

        self.__seEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.__seLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

        for se in self.survEvents.values():

            if self.getEaliestStart() > se.eventStart:
                self.setEaliestStart(se.eventStart)
            if self.getLatestEnd() < se.eventEnd:
                self.setLatestEnd(se.eventEnd)


class plottedSurveyEvents():

    # plotEvents = None
    # __peEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
    # __peLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def __init__(self):
        # self.plotEvents = {}
        self.plotEvents: Dict[str, surveyEvent] = {}
        self.__peEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.__peLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

    def getEaliestStart(self):
        return self.__peEarliestStart

    def getLatestEnd(self):
        return self.__peLatestEnd

    # def setEaliestStart(self, startDate):
    #     self.__peEarliestStart = startDate

    # def setLatestEnd(self, endDate):
    #     self.__peLatestEnd = endDate

    def clear(self):

        self.plotEvents.clear()
        self.updateMinMaxValues()

    def addSurveyEvent(self, objSE: surveyEvent, updateMinMax: bool = True):

        if objSE.eventName not in self.plotEvents:

            self.plotEvents[objSE.eventName] = objSE
            if updateMinMax:
                self.updateMinMaxValues()
            return True
        else:
            return False

    def removeSurveyEvent(self, nameSE: surveyEvent):

        if nameSE in self.plotEvents:
            self.plotEvents.pop(nameSE)
            self.updateMinMaxValues()
            return True
        return False

    def updateMinMaxValues(self):

        self.__peEarliestStart = datetime.strptime('2172-05-12', '%Y-%m-%d')
        self.__peLatestEnd = datetime.strptime('1972-05-12', '%Y-%m-%d')

        for pe in self.plotEvents.values():

            if self.getEaliestStart() > pe.eventStart:
                self.__peEarliestStart = pe.eventStart
            if self.getLatestEnd() < pe.eventEnd:
                self.__peLatestEnd = pe.eventEnd

    # def updateMinMaxValues(self):
        # pass

# class graphFDV(parentWidget):
