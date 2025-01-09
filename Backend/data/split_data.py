import json
import random

def split_data(input_file, train_file, dev_file, split_ratio=0.8):
    # 1. Read entire dataset
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. Shuffle to randomize
    random.shuffle(data)

    # 3. Compute split index
    split_index = int(len(data) * split_ratio)

    # 4. Slice
    train_data = data[:split_index]
    dev_data = data[split_index:]

    # 5. Write to separate files
    with open(train_file, "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2)

    with open(dev_file, "w", encoding="utf-8") as f:
        json.dump(dev_data, f, indent=2)

    print(f"Train set size: {len(train_data)}, Dev set size: {len(dev_data)}")

# Example usage:
if __name__ == "__main__":
    split_data(
        input_file="auto_labeled_output.json",
        train_file="train.json",
        dev_file="dev.json",
        split_ratio=0.8
    )
