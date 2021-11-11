import json


def learn_this(new_data, filename='dict.json'):
    with open(filename, 'r+') as file:
        # First we load existing data into a dict.
        file_data = json.load(file)
        # Join new_data with file_data inside emp_details
        file_data["dialogs"].append(new_data)
        # Sets file's current position at offset.
        file.seek(0)
        # convert back to json.
        json.dump(file_data, file, indent=4)

    # python object to be appended


user_input = input(">>> ")

new_data = {"tag": "new_tag",
            "triggers": [f"{user_input}"],
            "responses": ["new responses1", "new responses2"]
            }

learn_this(new_data)
