from traciSumo import TraciSumo
from graphData import GraphData

"""
    1 - Normal Sim // 2 - Efektli Sim
    sens : True/False -> False is not be for emergency 
"""

# 120 araç 14 acil 10sn duration

norm = TraciSumo(int=1, vehicle_id="all")
decd = TraciSumo(int=2, vehicle_id="all", sens=True)

GraphData(vehicle="All")
# GraphData(start_args=52)
# # GraphData(start_args=50)
# # GraphData(vehicle_id="t_0")
# # GraphData(vehicle_id="t_1")
# GraphData(vehicle_id="t_2")
# # GraphData(vehicle_id="t_4")
# GraphData(vehicle_id="t_80")
# # GraphData(vehicle_id="t_22")
# GraphData(vehicle_id="t_38 (Emergency)") # Emergency
# GraphData(vehicle_id="t_43 (Emergency)") # Emergency
# GraphData(vehicle_id="t_54 (Emergency)") # Emergency
# GraphData(vehicle_id="t_63")
# GraphData(vehicle_id="t_101 (Emergency)")