import os
import sys


def check_report_html():

    if os.path.exists("report.html") is not True:
        print("report.html file not exits")
        return 0
        
    try:
        with open("report.html", "r") as f:
            report_cont = f.read()
        if report_cont.find("failed results-table-row") != -1:
            print("chip or board support package test failed, please check it and repair!")
            return 1
    except Exception as err:
        print("Error message : {0}.".format(err))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(check_report_html())
