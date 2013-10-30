from getpass import getpass
from bs4 import BeautifulSoup
import mechanize
import time
import json


class Gold(object):

    def __init__(self):
        self.notify_email = None
        self.quarter = None
        self.user = None
        self.pw = getpass("UCSB NetID Password: ")
        searches = self.read_search_file("search.json")
        self.br = mechanize.Browser()

        while True:
            self.login()
            self.search(searches)
            self.wait()

    def login(self):
        while True:
            try:
                self.br.open("https://my.sa.ucsb.edu/gold/Login.aspx")
                # Select login form
                self.br.select_form(nr=0)
                form = self.br.form
                form['ctl00$pageContent$userNameText'] = self.user
                form['ctl00$pageContent$passwordText'] = self.pw
                self.br.find_control('ctl00$pageContent$CredentialCheckBox').items[0].selected = True
                response = self.br.submit()
                soup = BeautifulSoup(response.read())
                if soup.title.string == 'Login':
                    print("> Login unsuccessful. Check credentials.\n")
                    self.__init__()
                else:
                    print("> Login successful.")
                break
            except :
                print("Unexpected error logging in. Trying again...")


    def read_search_file(self, path):
        searches = None
        with open(path) as f:
            search_file = json.load(f)
            self.user = search_file["ucsb_net_id"]
            self.notify_email = search_file["notify_email"]
            self.mins_to_wait = float(search_file["mins_to_wait"])
            self.quarter = search_file["quarter"]
            searches = search_file["search_params"]

        blank = {"enroll_code" : "", "department" : "", "course_num" : ""}
        while True:
            try:
                searches.remove(blank)
            except ValueError:
                break
        return searches


    def search(self, searches):
        print("> Starting search...")
        for s in searches:
            try:
                self.br.open("https://my.sa.ucsb.edu/gold/CriteriaFindCourses.aspx")
                # Select search form
                self.br.select_form(nr=0)
                form = self.br.form
                # Set search params
                form['ctl00$pageContent$quarterDropDown'] = [self.quarter]
                form['ctl00$pageContent$enrollcodeTextBox'] = s['enroll_code']
                form['ctl00$pageContent$departmentDropDown'] = [s['department']]
                form['ctl00$pageContent$courseNumberTextBox'] = s['course_num']

                # Execute search and save result page for parsing
                soup = BeautifulSoup(self.br.submit().read())

                # Parse results
                error_page = soup.findAll("span", attrs={"id": "pageContent_messageLabel"})
                if error_page:
                    print("Class not found. Try searching again.")
                    self.search(searches)
                class_title = soup.findAll("span", attrs={"class": "tableheader"})
                info_header = soup.findAll("td", attrs={"class": "tableheader"})[0:7]
                info_table = soup.findAll("td", attrs={"class": "clcellprimary"})[0:7]

                info_dict = {}
                for title, detail in zip(info_header, info_table):
                    info_dict[title.string] = detail.string

                # Print class title
                title = class_title[0].string.replace(u'\xa0', u' ')
                title = ' '.join(title.split())
                print("\n%s" % title)
                s = "="
                for i in range(len(title)):
                    s += "="
                print("%s" % s)

                # Check if full
                if info_dict["Space"] == u"Full\xa0":
                    print("Class is full.")
                elif info_dict["Space"] == u"Closed\xa0":
                    print("Class closed. You should search for another class.")
                elif (float(info_dict["Space"]) / float(info_dict["Max"])) > 0:
                    print("Class is OPEN! Sending notification...")
                    self.notify(title)
                else:
                    print("Unknown reason why class is full.")
            except mechanize._form.ControlNotFoundError:
                print("error. skipping for now...\n")

    def notify(self, class_title):
        import smtplib
        fromaddr = self.user + "@umail.ucsb.edu"
        toaddrs  = self.notify_email
        msg = "\n[CLASS OPEN!]\n%s" % class_title

        username = fromaddr
        password = self.pw

        server = smtplib.SMTP('pod51019.outlook.com:587')
        server.starttls()
        server.login(username,password)
        server.sendmail(fromaddr, toaddrs, msg)
        server.quit()
        return self

    def wait(self):
        check_time = time.asctime(time.localtime(time.time()
                        + self.mins_to_wait*60))
        print("\n> Checking again at:\n> %s\n" % check_time)
        for i in range(int(self.mins_to_wait*60.0)):
            time.sleep(1)


def main():
    Gold()


if __name__ == "__main__":
    main()
