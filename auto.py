#!/usr/bin/python3

import textfsm
import pexpect
import os, sys, time
import json, jsondiff
import getch

def issueCommand(commands):
    child = pexpect.spawn('ssh vishal@192.168.56.103', encoding="utf-8")
    child.expect('Password:')
    child.sendline('Password')
    child.expect("#")
    child.sendline('term len 0')
    child.expect('#')
    for command in commands:
        child.sendline(command)
        child.expect('#')

def getJson(command=None):
    #logs in and executes the commands
    print("Connecting ...")
    child = pexpect.spawn('ssh vishal@192.168.56.103', encoding="utf-8")
    child.expect('Password:')
    child.sendline('Password')
    child.expect("#")
    os.system("clear")
    if not command:
        command = input(str(child.before) + "# ")
    child.sendline('term len 0')
    child.expect('#')
    child.sendline(command)
    child.expect('#')

    #collects the output
    cmd_show_data =  str(child.before)
    child.sendline('exit')

    #organizing the data with a template
    template = None

    try:
        with open("templates/" + command.replace(" ", "_") + ".textfsm") as tfsm:
            template = textfsm.TextFSM(tfsm)
    except FileNotFoundError:
        print("\"" + command + "\" is either not a valid command or is not supported currently.\n")
        getJson()
    output = template.ParseText(cmd_show_data)
    headers = template.header

    #converting data to JSON format
    structured_output = {}
    for array in output:
        structured_output[array[0]] = {}
        for i in range(1, len(array)):
            structured_output[array[0]][headers[i]] = array[i]

    #printing/saving JSON formatted data
    return (json.dumps(structured_output, indent=2, sort_keys=True), command)

def currentConfig():
    interfaces = json.loads(getJson("sh ip int br")[0])
    return interfaces

def configure(config=None):
    if not config:
        with open("config.json") as f:
            config = json.load(f)
    diff = jsondiff.diff(currentConfig(), config)
    print("Please confirm that this is the new configuration/changes:\n")
    print(diff)
    print("[y/n]:")
    if getch.getch().lower()[0] == "y":
        for key in diff:
            items = diff[key]
            for item in items:
                if item == "IP":
                    issueCommand(["config term", "int " + key, "ip addr " + items[item]])
        print("Successfully configured the machine!")
        time.sleep(2)

def optionChooser(again=False):
    try:
        if not again:
            print("Actions:\n\n(q) Quit\n(1) Get output of a command\n(2) Configure a machine from JSON\n")
        chooser = getch.getch().lower()
        if chooser == '\x7f':
            optionChooser(True)
        if chooser not in ["q", "1", "2"]:
            print("Invalid Option, please try again.")
            optionChooser(True)
        return chooser
    except ValueError:
        print("Invalid Option, please try again.")
        optionChooser(True)

def save(json_output, command):
    with open("output/" + command + ".json", "w+") as json_file:
        json_file.write(json_output)
    print("Successfully saved output!")

def main():
    os.system("clear")
    option = optionChooser()
    os.system("clear")
    if option == "q":
        print("Goodbye!")
        sys.exit(0)
    if option == "1":
        output = getJson()
        print(output[0])
        print("\n\n")
        if input("Do you want to save this output(This will overwrite the previous output of this command)? ").lower()[0] == "y":
            save(output[0], output[1])
    if option == "2":
        configure()
    main()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        os.system("clear")
        print("Goodbye!")
