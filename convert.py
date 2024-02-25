import csv

input_filename = 'output2.csv'
output_filename = 'merged_output.csv'

with open(input_filename, 'r', newline='') as infile, open(output_filename, 'w', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    for row in reader:
        merged_column = row[0] + '/' + row[1]
        
        new_row = [merged_column] + row[2:]
        
        writer.writerow(new_row)

print(f'Data merged and saved to {output_filename}')
