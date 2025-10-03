import pandas as pd

import config


class MainGen:
    def __init__(self):
        self.DATA_FILE = config.DATA_FILE

        self.data = config.load_data(self.DATA_FILE)
        self.main()

    def main(self):
        result = []

        if pd.isna(self.data):
            return

        for data_key in self.data.keys():
            for data_chs in self.data[data_key]:
                result_row = ["" for i in range(6)]
                for key_value, value in dict(data_chs).items():
                    if key_value == "dse": result_row[0] = value
                    if key_value == "problem_type": result_row[1] = value
                    if key_value == "description": result_row[2] = value
                    if key_value == "date_time":
                        result_row[3] = str(value)[:10]
                        result_row[4] = str(value)[11:19]
                    if key_value == "user_id": result_row[5] = value
                result.append(result_row)
        for i in result:
            print(i)


if __name__=="__main__":
    run = MainGen()