import os
import sys
import optparse
import traci
import sumolib
import numpy as np
from random import randint
import matplotlib.pyplot as plt
import pandas as pd
import tkinter as tk
import csv
from tkinter import ttk

class GraphData:
    def __init__(self, vehicle_id=False, start_args=False, vehicle="All"):
        self.createData()
        if vehicle_id:
            self.chart(vehicle_id=vehicle_id)
        elif start_args:
            self.chart_All(start_args=start_args)
        else:
            self.chart_All(vehicle=vehicle)

    def createData(self):
        self.vehicleState = {}

        def data(lines):
            for line in lines:
                if "Simulation" in line:
                    sim = line.split(" ")[0]
                    self.vehicleState[sim] = {}
                elif "Vehicle ID" in line:
                    vehicle_id = line.split(":")[1].split("\n")[0].strip()
                    self.vehicleState[sim][vehicle_id] = {}
                elif "Step" in line:
                    try:
                        self.vehicleState[sim][vehicle_id]["Step"]
                        self.vehicleState[sim][vehicle_id]["Speed"]
                    except:
                        self.vehicleState[sim][vehicle_id]["Step"] = []
                        self.vehicleState[sim][vehicle_id]["Speed"] = []
                    finally:
                        step = line.split(":")[1].split("\t")[0].strip()
                        speed = line.split(":")[2].strip()
                        self.vehicleState[sim][vehicle_id]["Step"].append(int(step))
                        self.vehicleState[sim][vehicle_id]["Speed"].append(int(float(speed) * 10))

        filePath_n = os.path.join(os.getcwd(), "code\\dataVehicleState_normal.txt")
        with open(filePath_n, 'r') as file:
            lines = file.readlines()
        data(lines)

        filePath_d = os.path.join(os.getcwd(), "code\\dataVehicleState_decide.txt")
        with open(filePath_d, 'r') as file:
            lines = file.readlines()
        data(lines)

    def chart(self, vehicle_id):
        # Graph
        fig, ax = plt.subplots(1)

        min_step = min(min(self.vehicleState["Normal"][vehicle_id]["Step"]), min(self.vehicleState["Decide"][vehicle_id]["Step"]))
        max_step = max(max(self.vehicleState["Normal"][vehicle_id]["Step"]), max(self.vehicleState["Decide"][vehicle_id]["Step"]))

        common_steps = list(range(min_step, max_step + 1))
        normal_speeds = [speed for speed in self.vehicleState["Normal"][vehicle_id]["Speed"]]
        normal_data = [
            normal_speeds[self.vehicleState["Normal"][vehicle_id]["Step"].index(step)]
            if step in self.vehicleState["Normal"][vehicle_id]["Step"]
            else -1
            for step in common_steps
        ]

        # Decide verileri
        decide_speeds = [speed for speed in self.vehicleState["Decide"][vehicle_id]["Speed"]]
        decide_data = [decide_speeds[self.vehicleState["Decide"][vehicle_id]["Step"].index(step)] 
            if step in self.vehicleState["Decide"][vehicle_id]["Step"]
            else -1
            for step in common_steps
        ]

        valid_normal_data = [speed for speed in normal_data if speed != -1]
        valid_decide_data = [speed for speed in decide_data if speed != -1]

        folder_name = "excel"

        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        csv_filename = os.path.join(folder_name, f"{vehicle_id}.csv")

        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = ['Step', 'Normal_Speed', 'Decide_Speed']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()
            size = len(valid_normal_data)
            valid_decide_datas = np.array(valid_decide_data)
            valid_decide_datas.resize(size)
            valid_decide_datas[size:] = -1

            # Write data
            for step, normal_speed, decide_speed in zip(common_steps[:len(valid_normal_data)], valid_normal_data, valid_decide_datas):
                writer.writerow({'Step': step, 'Normal_Speed': normal_speed, 'Decide_Speed': decide_speed})

        ax.plot(common_steps[:len(valid_normal_data)], valid_normal_data, label='Speed for step (Normal)', color='red', ls='-')
        ax.plot(common_steps[:len(valid_decide_data)], valid_decide_data, label='Speed for step (Decide)', color='green', ls='--')
        ax.legend(loc='upper left')
        ax.set_title(f"Vehicle ID: {vehicle_id}")
        ax.set_xlabel('Steps')
        ax.set_ylabel('Speeds')
        ax.grid()
        plt.show()

    def chart_All(self, start_args=False, vehicle="All"):
        vehicles = [vehicle_id for vehicle_id, vehicle_data in self.vehicleState["Normal"].items()]
        if start_args:

            # Graph
            fig, ax = plt.subplots()

            bar_width = 0.2
            colors = ["#3787C9", "#DE7775", "#30CF55", "#DE7775"]
            labels = ["Normal Sim", "Waiting Time", "Effective Sim", "Waiting Time"]

            x = np.arange(0,10)

            folder_name = "excel"

            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            csv_filename = os.path.join(folder_name, f"t_{start_args}-t_{start_args+9}.csv")

            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ['id', 'Normal Step', 'Normal Wait', 'Effektive Step', 'Effektive Wait']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                writer.writeheader()

                for i, vehicle_id in enumerate(vehicles[start_args:start_args+10]):
                    bar_1 = len(np.arange(min(self.vehicleState["Normal"][vehicle_id]["Step"]),max(self.vehicleState["Normal"][vehicle_id]["Step"])))
                    bar_2 = len([speed for speed in self.vehicleState["Normal"][vehicle_id]["Speed"] if speed == 0])
                    bar_3 = len(np.arange(min(self.vehicleState["Decide"][vehicle_id]["Step"]),max(self.vehicleState["Decide"][vehicle_id]["Step"])))
                    bar_4 = len([speed for speed in self.vehicleState["Decide"][vehicle_id]["Speed"] if speed == 0])

                    writer.writerow({'id': vehicle_id,'Normal Step': bar_1, 'Normal Wait': bar_2, 'Effektive Step': bar_3, 'Effektive Wait': bar_4})

                    if i == 0:
                        ax.bar(x[i] - 1.5 * bar_width, bar_1, color=colors[0], width=bar_width, edgecolor="white", linewidth=0.5, label=f'{labels[0]} - {vehicle_id}')
                        ax.bar(x[i] - 0.5 * bar_width, bar_2, color=colors[1], width=bar_width, edgecolor="white", linewidth=0.5, label=labels[1])
                        ax.bar(x[i] + 0.5 * bar_width, bar_3, color=colors[2], width=bar_width, edgecolor="white", linewidth=0.5, label=labels[2])
                        ax.bar(x[i] + 1.5 * bar_width, bar_4, color=colors[3], width=bar_width, edgecolor="white", linewidth=0.5)
                    else:
                        ax.bar(x[i] - 1.5 * bar_width, bar_1, color=colors[0], width=bar_width, edgecolor="white", linewidth=0.5, label=vehicle_id)
                        ax.bar(x[i] - 0.5 * bar_width, bar_2, color=colors[1], width=bar_width, edgecolor="white", linewidth=0.5)
                        ax.bar(x[i] + 0.5 * bar_width, bar_3, color=colors[2], width=bar_width, edgecolor="white", linewidth=0.5)
                        ax.bar(x[i] + 1.5 * bar_width, bar_4, color=colors[3], width=bar_width, edgecolor="white", linewidth=0.5)

            ax.legend(loc='upper left')

            ax.set_title(f"All Vehicle")
            ax.set_xlabel('Vehicles')
            ax.set_ylabel('Steps')
            ax.grid()

            plt.show()
        else:
            master = tk.Tk()
            master.geometry("800x600")

            folder_name = "excel"

            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            csv_filename = os.path.join(folder_name, f"all_vehicle.csv")

            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ["Vehicle ID", "Normal Sim Step", "Normal Sim Stop", "N Waiting %", "Effektive Sim Step", "Effektive Sim Stop", "E Waiting %", "Success %"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                writer.writeheader()

                data = []
                unsuccessCount = 0
                count = len(vehicles)
                emergencySumSuccess = 0
                emergencyCount = 0
                percentileSumSuccess = 0
                for vehicle_id in vehicles:
                    # for vehicle_id in vehicles[start:start+20]:
                    normal_step = len(np.arange(min(self.vehicleState["Normal"][vehicle_id]["Step"]),
                                                max(self.vehicleState["Normal"][vehicle_id]["Step"])))
                    normal_stop = len([speed for speed in self.vehicleState["Normal"][vehicle_id]["Speed"] if speed == 0])
                    normal_percentile = format((normal_stop / normal_step) * 100, '.2f')
                    decide_step = len(np.arange(min(self.vehicleState["Decide"][vehicle_id]["Step"]),
                                                max(self.vehicleState["Decide"][vehicle_id]["Step"])))
                    decide_stop = len([speed for speed in self.vehicleState["Decide"][vehicle_id]["Speed"] if speed == 0])
                    decide_percentile = format((decide_stop / decide_step) * 100, '.2f')
                    nsp = float(normal_percentile)
                    dsp = float(decide_percentile)
                    percentile = format(100-((100-nsp) / (100-dsp) * 100), '.2f') if dsp < nsp else "NOT SUCCESS"
                    unsuccessCount += 1 if percentile == "NOT SUCCESS" else 0

                    if "Emergency" in vehicle_id:
                        emergencyCount += 1
                        if percentile != "NOT SUCCESS":
                            emergencySumSuccess += float(percentile)
                    
                    success = float(percentile) if percentile != "NOT SUCCESS" else 0
                    percentileSumSuccess += success

                    data.append([vehicle_id, normal_step, normal_stop, normal_percentile, decide_step, decide_stop, decide_percentile, percentile])
                    writer.writerow({"Vehicle ID":vehicle_id, "Normal Sim Step":normal_step, "Normal Sim Stop":normal_stop, "N Waiting %":normal_percentile, "Effektive Sim Step":decide_step, "Effektive Sim Stop":decide_stop, "E Waiting %":decide_percentile, "Success %":percentile})

                projectSuccess = float(format((count-unsuccessCount)/count*100, ".2f"))
                meanSuccess = float(format(percentileSumSuccess/count, ".2f"))
                meanEmergencySuccess = float(format(emergencySumSuccess/emergencyCount, ".2f"))

            folder_name = "excel"

            if not os.path.exists(folder_name):
                os.makedirs(folder_name)

            csv_filename = os.path.join(folder_name, f"all_vehicle_stats.csv")

            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ["Vehicle Count", "Emergency Count", "Unsuccess Vehicle", "Mean Success %", "Mean Emergency Success %", "Project Success %"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                # Write header
                writer.writeheader()
                writer.writerow({"Vehicle Count":count, "Unsuccess Vehicle":unsuccessCount, "Mean Success %":meanSuccess, "Project Success %":projectSuccess, "Emergency Count":emergencyCount, "Mean Emergency Success %":meanEmergencySuccess})

            df = pd.DataFrame(data, columns=["Vehicle ID", "Normal Sim Step", "Normal Sim Stop", "N Waiting %", "Effektive Sim Step", "Effektive Sim Stop", "E Waiting %", "Success %"])

            master.title("Vehicle State Table")

            # Create a canvas widget
            canvas = tk.Canvas(master)
            canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            # Create a treeview widget inside the canvas
            tree = ttk.Treeview(canvas, columns=list(df.columns), show="headings")

            # Add a vertical scrollbar
            yscrollbar = ttk.Scrollbar(canvas, orient="vertical", command=tree.yview)
            yscrollbar.pack(side="right", fill="y")
            tree.configure(yscrollcommand=yscrollbar.set)

            colors = ["#41D0DD", "#1125FE", "#FF2243", "#DBCC57", "#67FF20", "#FF2243", "#DBCC57", "#57DBCE"]
            for i, (col, color) in enumerate(zip(df.columns, colors)):
                tree.heading(col, text=col, anchor="center", command=lambda c=col: sort_treeview(tree, c, False))
                tree.column(col, width=100, anchor="center", stretch=tk.NO)
                tree.tag_configure(f"col_{i}", background=color)
                tree.heading(col, text=col, anchor="center", command=lambda c=col: sort_treeview(tree, c, False))

            # Insert data into the treeview
            for i, row in df.iterrows():
                tree.insert("", "end", values=list(row))

            # Embed the treeview inside the canvas
            canvas.create_window(0, 0, window=tree, anchor="nw", width=1000, height=750)

            # Configure the canvas scrolling region
            canvas.update_idletasks()
            tree.update_idletasks()
            canvas.config(scrollregion=canvas.bbox("all"))

            def sort_treeview(tv, col, reverse):
                l = [(tv.set(k, col), k) for k in tv.get_children('')]
                l.sort(reverse=reverse)

                # rearrange items in sorted positions
                for index, (val, k) in enumerate(l):
                    tv.move(k, '', index)

                # reverse sort next time
                tv.heading(col, command=lambda: sort_treeview(tv, col, not reverse))


            master.mainloop()

