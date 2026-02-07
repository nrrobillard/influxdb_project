import yaml
from datetime import datetime, timedelta

# Define your waterPlants() function
def waterPlants(plant_name):
    print(f"Watering {plant_name}!")

# Path to the YAML file storing last watered times
yaml_file = "plants_watered.yml"

def load_last_watered_times(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as file:
        return yaml.safe_load(file)

def save_last_watered_times(file_path, watered_times):
    with open(file_path, "w") as file:
        yaml.safe_dump(watered_times, file)

def check_and_water_plants(plants, file_path):
    last_watered_times = load_last_watered_times(file_path)
    now = datetime.now()

    for plant in plants:
        last_watered = last_watered_times.get(plant)
        if not last_watered or now - datetime.fromisoformat(last_watered) > timedelta(hours=72):
            waterPlants(plant)
            last_watered_times[plant] = now.isoformat()
        else:
            hours_left = 72 - (now - datetime.fromisoformat(last_watered)).total_seconds() // 3600
            print(f"{plant} doesn't need water yet. Wait for another {hours_left:.1f} hours.")

    save_last_watered_times(file_path, last_watered_times)

def main():
    # List of plant names
    plants = ["plant1", "plant2", "plant3", "plant4"]
    check_and_water_plants(plants, yaml_file)

if __name__ == "__main__":
    main()