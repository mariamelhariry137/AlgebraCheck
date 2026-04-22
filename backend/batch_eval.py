import json

def fix_indexing(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Update only the entry_index
        for index, item in enumerate(data):
            item['entry_index'] = index

        with open(output_file, 'w', encoding='utf-8') as f:
            # ensure_ascii=False preserves symbols like ± and √
            # indent=2 keeps your current pretty-print format
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print(f"Success! Fixed {len(data)} entries in {output_file}")

    except FileNotFoundError:
        print(f"Error: Could not find {input_file}. Make sure it's in the same folder.")

# Execute the script on your file
fix_indexing(r'C:\mariam\uni\bachelor\algebra-error-detector\eval_results2.json', 'eval_results2_fixed.json')