

from app import app, db

#***** DBのリスト作成*******#
def GetPullDownList(TABLE, colCODE, colNAME, OrderCol):
    
    GetList = []
    dblist = db.session.query(TABLE, colCODE.label("CODE"), colNAME.label("NAME") ).order_by(OrderCol)
    GetList.append(["", ""])
    for row in dblist:
        GetList.append([row.CODE, row.NAME])

    return GetList

#***** DBdata取得*******#
def GetData(TABLE, colCODE, colNAME, OrderCol):
    
    GetList = []
    dblist = db.session.query(TABLE, colCODE.label("CODE"), colNAME.label("NAME") ).order_by(OrderCol)
    GetList.append([0, ""])
    for row in dblist:
        GetList.append([row.CODE, row.NAME])

    return GetList

#***** DBdataShot付き取得*******#
def GetDataS(TABLE, colCODE, colNAME, OrderCol):
    
    GetList = []
    dblist = db.session.query(TABLE, colCODE.label("CODE"), colNAME.label("SHORTNAME") ).order_by(OrderCol)
    GetList.append([0, ""])
    for row in dblist:
        GetList.append([row.CODE, row.SHORTNAME])

    return GetList

#DB登録用　int型が空白だったらNoneを代入
def intCheck(intValue):
    
    if str.isnumeric(intValue):
        return intValue
    else:
        intValue = None
        return intValue

def blankCheck(strValue):

    if strValue != '' and strValue != '0':
        return strValue
    else:
        strValue = None
        return strValue

# html表示用
def NoneCheck(strValue):

    if strValue == None:
        strValue = ''
        return strValue
    else:
        return strValue
    
def TimeCheck(strValue):
    if strValue == '':
        strValue = '00:00'
        return strValue
    else:
        return strValue
    
def ZeroCheck(strValue):
    if strValue == None or strValue == '':
        strValue = '0'
        return strValue
    else:
        return strValue