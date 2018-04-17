import requests
import traceback
import json
from dateutil.parser import parse

base_url = "https://mazak.jct.ac.il"


class LoginErrorExcpetion(Exception):
    pass


class BlockedStudent(Exception):
    pass


def log_to_mazak(username, password):
    session = requests.Session()
    login_data = {"username": username, "password": password}
    r = session.post(base_url + "/api/home/login.ashx?action=TryLogin", data=login_data)
    data = json.loads(r.text)
    if not data["success"]:
        raise LoginErrorExcpetion("pass not correct")
    return session
    # print(e.format_exc())


def get_grades(session):
    r = session.post(base_url + "/api/student/grades.ashx?action=LoadGrades",
                     data={"selectedAcademicYear": "null", "selectedSemester": "null", "pageSize": "99999999"})
    data = json.loads(r.text)
    return data["items"]


def get_grade(session, course_id):
    r = session.post(base_url + "/api/student/coursePartGrades.ashx?action=GetStudentCoursePartGrades",
                     data={"actualCourseId": str(course_id)})
    data = json.loads(r.text)
    return data


def get_all_protecting_grades(grade):
    return [part for part in grade["partGrades"] if part["minGrade"] == 0]


def calc_grade_without_prot_parts(grade):
    final_grade = 0.0
    final_weight = 0.0
    for part in grade["partGrades"]:
        if part["minGrade"] != 0:  # not protection part
            part_grade = 0
            try:
                if part["gradeCName"] is not None:
                    part_grade = float(part["gradeCName"])
                elif part["gradeSpecialName"] is not None:
                    part_grade = float(part["gradeSpecialName"])
                elif part["gradeBName"] is not None:
                    part_grade = float(part["gradeBName"])
                elif part["gradeAName"] is not None:
                    part_grade = float(part["gradeAName"])
            except:
                part_grade = 0
            if part_grade == 0:
                return "חסר"
            final_grade += (float(part["weight"]) / 100) * part_grade
            final_weight += float(part["weight"])
    if final_grade != 0:
        return int(final_grade + 0.5 + 100 - final_weight)
    return "חסר"


def calc_final_grade_protection(grade):
    prot_parts = get_all_protecting_grades(grade)
    final_grade_parts = grade["partGrades"]
    grade_without_parts = calc_grade_without_prot_parts(grade)
    for prot_part in prot_parts:
        try:
            if prot_part["gradeCName"] is not None:
                part_grade = float(prot_part["gradeCName"])
            elif prot_part["gradeSpecialName"] is not None:
                part_grade = float(prot_part["gradeSpecialName"])
            elif prot_part["gradeBName"] is not None:
                part_grade = float(prot_part["gradeBName"])
            elif prot_part["gradeAName"] is not None:
                part_grade = float(prot_part["gradeAName"])
        except:
            part_grade = 0
        if part_grade <= grade_without_parts:
            final_grade_parts.remove(part_grade)
    grade["partGrades"] = final_grade_parts
    return calc_final_grade(grade)


def calc_final_grade(grade):
    final_grade = 0.0
    for part in grade["partGrades"]:
        part_grade = 0
        try:
            if part["gradeCName"] is not None:
                part_grade = float(part["gradeCName"])
            elif part["gradeSpecialName"] is not None:
                part_grade = float(part["gradeSpecialName"])
            elif part["gradeBName"] is not None:
                part_grade = float(part["gradeBName"])
            elif part["gradeAName"] is not None:
                part_grade = float(part["gradeAName"])
        except:
            part_grade = 0
        if part_grade == 0:
            return "חסר"
        final_grade += (float(part["weight"]) / 100) * part_grade
    if final_grade != 0:
        return int(final_grade + 0.5)
    return "חסר"


def grade_to_string(grade):
    output_text = ["{} :".format(grade["actualCourse"]["courseName"])]
    for part in grade["partGrades"]:
        grade_string_template = "\nציון ({}) : {}"
        grade_string = ""
        if part["gradeCName"] is not None:
            grade_string += grade_string_template.format("ג", part["gradeCName"])
        if part["gradeSpecialName"] is not None:
            grade_string += grade_string_template.format("מיוחד", part["gradeSpecialName"])
        if part["gradeBName"] is not None:
            grade_string += grade_string_template.format("ב", part["gradeBName"])
        if part["gradeAName"] is not None:
            grade_string += grade_string_template.format("א", part["gradeAName"])
        else:
            grade_string = grade_string.format("-", "חסר")
        output_text.append("""
{} :
{}
משקל : {}
        """.format(part["gradePartTypeName"], grade_string, part["weight"]))
    return output_text


def get_avereges(session):
    r = session.post(base_url + "/api/student/Averages.ashx?action=LoadData")
    data = json.loads(r.text)
    if not data["success"]:
        raise Exception("Error getting avereges")
    return data


def avereges_to_string(avg):
    datadict = avg["academicAverages"][0]
    academicAvg = datadict["academicCumulativeAverage"]
    academicNz = datadict["academicCumulativeCredits"]
    academicWeight = datadict["academicWeight"]
    Kodeshavg = datadict["kodeshCumulativeAverage"]
    kodeshWeight = datadict["kodeshWeight"]
    allAvg = datadict["graduateCumulativeAverage"]
    allNz = datadict["graduateCumulativeCredits"]
    m = parse(datadict["calcDate"])
    calcDate = str(m).replace("+02:00", "")
    total = """
    ממוצע אקדמי : {}
    נ''ז אקדמיות : {}
    משקל אקדמי : {}

    ממוצע קודש : {}
    משקל קודש : {}

    ממוצע מצטבר : {}
    נ''ז מצטבר : {}

    תאריך חישוב : {}
""".format(academicAvg, academicNz, academicWeight, Kodeshavg, kodeshWeight, allAvg, allNz, calcDate)
    result_list = [total]
    for year in avg["yearlyDepartmentAverage"]:
        yr = year["academicYearName"]
        avg = year["average"]
        nz = year["accumulatedCredits"]
        date = str(parse(year["calculatedOn"])).replace("+02:00", "")
        output = """
        שנה אקדמית : {}
        ממוצע אקדמי : {}
        נ''ז אקדמיות : {}
        חושב ב : {}
            """.format(yr, avg, nz, date)
        result_list.append(output)

    return result_list


def get_test_confirmations(session):
    r = session.post(base_url + "/api/student/certificates.ashx?action=LoadDataForTestCertificate")
    data = json.loads(r.text)
    if data["isStudentBlocked"]:
        raise BlockedStudent("Student Blocked")
    tests = data["tests"]
    file_list = []
    for test in tests:
        r = session.get(
            base_url + '/api/student/certificates.ashx?action=DownloadTestCertificate&academicYearId={}&semesterId={}'.format(
                test["academicYearId"], test["semesterId"]),
            stream=True)
        file_name = "אישור נבחן {} {}".format(test["academicYearName"], test["semesterName"]).replace("\"", "") + '.pdf'
        out = bytes()
        for block in r.iter_content(1024):
            out += block
        file_list.append((out, file_name))
    return file_list


def get_available_notebooks(session):
    r = session.post(base_url + "/api/student/testNotebooks.ashx?action=SearchQuery",
                     data={"selectedAcademicYear": "null", "selectedSemester": "null", "selectedTestTimeType": "null",
                           "pageSize": "99999999"})
    data = json.loads(r.text)
    return data["items"]


def get_notebook(session, notebook_id):
    r = session.get(base_url + "/api/student/testNotebooks.ashx?action=DownloadNotebook&notebookId=" + str(notebook_id),
                    stream=True)
    out = bytes()
    for block in r.iter_content(1024):
        out += block
    return out


def get_departments(session):
    link = "/api/student/certificates.ashx?action=LoadDataForGradesSheet"
    r = session.post(base_url + link)
    data = json.loads(r.text)
    return data["departments"]


def get_grade_sheet(session, dept_id, lang):
    r = session.get(
        base_url + "/api/student/certificates.ashx?action=DownloadGradesSheet&selectedLanguage={}&showMore=true&selectedDepartment={}".format(
            lang, dept_id),
        stream=True)
    out = bytes()
    for block in r.iter_content(1024):
        out += block
    return out


if __name__ == '__main__':
    with open("pass", "r+") as f:
        un = f.readline().rstrip('\n')
        pw = f.readline().rstrip('\n')
    s = log_to_mazak(un, pw)
    # x = get_notebook(s,269276)
    grade = get_grade(s, 23492)
    print(calc_final_grade_protection(grade))
    for text in grade_to_string(grade):
        print(text)
