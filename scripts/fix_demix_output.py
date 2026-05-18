import os

demixed_dir = 'all_sra_outputs/demixed'

for file in os.listdir(demixed_dir):
    if file.endswith('.demixed'):
        file_path = os.path.join(demixed_dir, file)
        out_path = file_path
    elif file.endswith('.demix.tsv'):
        file_path = os.path.join(demixed_dir, file)
        base = file[: -len('.demix.tsv')]
        out_path = os.path.join(demixed_dir, base + '.demixed')
    else:
        continue

    with open(file_path, 'r') as f:
        lines = f.readlines()
    line_fixed = lines[0].replace('.variants.tsv', '_variants.tsv')
    with open(out_path, 'w') as f:
        f.write(line_fixed)
        for line in lines[1:]:
            f.write(line)
    if file_path != out_path:
        os.remove(file_path)
