import sys
import re
import matplotlib.pyplot as plt
from enum import Enum


class SizePrefix(Enum):
    B = 'B'
    KB = 'KB'
    MB = 'MB'
    GB = 'GB'
    TB = 'TB'


def size_from_prefix(prefix: SizePrefix) -> int:
    match prefix:
        case SizePrefix.B: 
            return 1
        case SizePrefix.KB: 
            return 1024
        case SizePrefix.MB: 
            return 1024 ** 2
        case SizePrefix.GB: 
            return 1024 ** 3
        case SizePrefix.TB: 
            return 1024 ** 4


def get_size(value: str) -> int:
    pattern = r'(\d+)(\D+)'
    matches = re.match(pattern, value)
    if matches:
        try:
            number_part = matches.group(1)  
            prefix_part = matches.group(2) 
            return int(number_part) * size_from_prefix(SizePrefix(prefix_part))
        except:
            pass


class SizeDistribution:
    def __init__(self, batches: list) -> None:
        self.aggregated_table = {val:0 for val in batches}
        self.aggregated_bounds = {}
        for key in self.aggregated_table.keys():
            bounds = key.split('-')
            size_bounds = tuple(get_size(bound) for bound in bounds[:2])
            self.aggregated_bounds[key] = size_bounds

    def add_by_size(self, size, number):
        for key in self.aggregated_table.keys():
            if size >= self.aggregated_bounds[key][0] and size < self.aggregated_bounds[key][1]:
                self.aggregated_table[key] += number
                break

    def save_gistogram(self, filename):
        plt.figure(figsize=(16, 10))

        splitted_sizes = ['-\n'.join(val.split('-')) for val in self.aggregated_table.keys()]
        plt.bar(splitted_sizes,
                self.aggregated_table.values(),
                color='blue')

        for x, y in zip(splitted_sizes, self.aggregated_table.values()):
            plt.text(x, y, f'{y}', ha='center', va='bottom', fontsize=14, color='darkblue')

        plt.xlabel("File Size", fontsize=14)  
        plt.ylabel("Number of files", fontsize=14)
        plt.xticks(fontsize=12)  
        plt.yticks(fontsize=12)
        plt.gca().spines["top"].set_visible(False)  
        plt.gca().spines["right"].set_visible(False)
        plt.savefig(filename) 
        plt.close()


class FilesAnalyzer:
    def __init__(self, file_path: str) -> None:
        self.data_list = []
        self.plain_table = {}
        self.total_space_usage = 0
        self.total_files = 0
        self.load_from_file(file_path)

    def load_from_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    size = int(line.split()[0])
                    self.data_list.append(size)
                    self.plain_table[size] = self.plain_table.get(size, 0) + 1

            self.total_space_usage = sum([int(k) * v for k, v in self.plain_table.items()])
            self.total_files = sum([v for v in self.plain_table.values()])

        except FileNotFoundError:
            print(f"File {sys.argv[1]} not found")

    def generate_gistogram(self, batches, filename):
        distribution = SizeDistribution(batches)

        for key, value in self.plain_table.items():
            distribution.add_by_size(key, value)

        distribution.save_gistogram(filename)
        
    

if __name__ == "__main__":

    files_analyzer = FilesAnalyzer('res.txt')

    distributions = [
        ['0B-128B','128B-256B','256B-512B','512B-1KB','1KB-2KB', '2KB-8KB','8KB-16KB','16KB-64KB','64KB-256KB','256KB-1MB','1MB-16MB','16MB-128MB','128MB-512MB','512MB-16TB'],
        ['0B-512B','512B-1KB','1KB-2KB','2KB-4KB','4KB-8KB','8KB-16KB','16KB-32KB','32KB-64KB', '64KB-128KB','128KB-256KB','256KB-512KB','512KB-1MB','1MB-2MB','2MB-4MB','4MB-8MB','8MB-16TB'],
        ['0B-1KB','1KB-2KB','2KB-3KB','3KB-4KB','4KB-5KB','5KB-6KB','6KB-7KB','7KB-8KB','8KB-9KB','9KB-10KB','10KB-11KB','11KB-12KB','12KB-13KB','13KB-14KB','14KB-15KB','15KB-16KB',
         '16KB-64KB', '64KB-256KB','256KB-1MB','1MB-16MB','16MB-512MB','512MB-16TB']
    ]

    for idx, distribution in enumerate(distributions):
        file_name = f'gistogram_{idx+1}.png'
        files_analyzer.generate_gistogram(distribution, file_name)
        print(f"Гістограму збережено: ", file_name)

    print("Кількість файлів: ", files_analyzer.total_files)
    print("Обсяг зайнятої пам'яті (байт): ", files_analyzer.total_space_usage)

    sorted_sizes = {k: v for k, v in sorted(files_analyzer.plain_table.items(), key=lambda item: item[0])}

    #for d in range(16384, 131073, 16384):
    for d in range(1024, 16384, 1024):
        best_percentage = 0
        best_a, best_b = None, None 

        sorted_list = sorted(files_analyzer.data_list)
        files_num = files_analyzer.total_files
        idx = 0
        while idx <= files_num:
            a = sorted_list[idx]

            p = int(idx + (files_num - idx) / 2)
            p_prev = idx
            while not p_prev == p:
                if sorted_list[p] - a > d:
                    tmp = p
                    p = int(p - abs(p - p_prev) / 2)
                    p_prev = tmp
                elif sorted_list[p] - a < d:
                    tmp = p
                    p = int(p + abs(p_prev - p) / 2)
                    p_prev = tmp
                else:
                    break
            percentage_in_range = ((p-idx) / files_analyzer.total_files) * 100
            if percentage_in_range > best_percentage:
                best_percentage = percentage_in_range
                best_a, best_b = idx, p
            
            idx+=1000

        print(f"Відсоток файлів у діапазоні від {sorted_list[best_a]} до {sorted_list[best_b]} байт: {best_percentage:.2f}%")

    