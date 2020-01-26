from flask import Flask , request , jsonify
from flask_restful import Resource , Api
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)
api = Api(app)

def parseAttendance(data):
  cols = data.find_all('td')
  return {
      'sno':cols[0].text,
      'subject':cols[1].text,
      'lec+tut':cols[2].find('a').text if cols[2].find('a') else '',
      'lec':cols[3].find('a').text if cols[3].find('a') else '',
      'tut':cols[4].find('a').text if cols[4].find('a') else '',
      'prac':cols[5].find('a').text if cols[5].find('a') else '',
  }

def webkiosk_login(e_no , dob , password):
  with requests.session() as s:
    p = s.get('https://webkiosk.jiit.ac.in/index.jsp')
    login_page = BeautifulSoup(p.content , 'html.parser')
    captcha = login_page.findAll('table')[-3].find('font').contents[0]
    print(captcha)
    # headers = {
    #     "Content-Type": "application/x-www-form-urlencoded",
    #     "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36",
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    #     "Cookie": "JSESSIONID=" + s.cookies.values()[0]
    # }
    payload = {
        'x': '', 
        'txtInst': 'Institute',
        'InstCode': 'JIIT',
        'txtuType': 'Member Type',
        'UserType101117': 'S',
        'txtCode': 'Enrollment No',
        'MemberCode': e_no,
        'DOB': 'DOB',
        'DATE1': dob,
        'txtPin': 'Password/Pin',
        'Password101117': password,
        'txtCode': 'Enter Captcha',    
        'txtcap': captcha,
        'BTNSubmit': 'Submit'
    }
    res = s.post('https://webkiosk.jiit.ac.in/CommonFiles/UseValid.jsp' , data=payload)
    res = s.get('https://webkiosk.jiit.ac.in/StudentFiles/Academic/StudentAttendanceList.jsp')
    dashboard = BeautifulSoup(res.content , 'html.parser')
    # print(dashboard.prettify())
    att_table_parsed = dashboard.find_all('tr')[4:-1]
    attendance = list(map(parseAttendance , att_table_parsed))
    # print(att_table_parsed[0].find_all('td')[3].find('a').text)

    return attendance

def timetable_api(batch, attendance):
  subjects = []
  for data in attendance:
    if data["subject"].split(" - ")[0] == "MINOR PROJECT-2":
      continue
    subjects.append(data["subject"].split(" - ")[0])
  res = requests.post('https://jiit-timetable.herokuapp.com/v2', json={'batch': batch, 'enrolled_courses': subjects})
  return res.json()["result"]

class AttendanceApi(Resource):
    def post(self):
        data = request.get_json()
        attendance = webkiosk_login(data['eno'] , data['dob'] , data['password'])
        timetable = timetable_api(data['batch'] , attendance)
        return {'attendance' : attendance , 'timetable' : timetable} , 201

api.add_resource(AttendanceApi , '/')

if __name__ == '__main__':
    app.run(host='192.168.1.201',debug=False)
    # app.run()