def calculate_workers_to_split_trembl_file(workers_number: int) -> int:
    workers_number_for_small_files = 1
    trembl_workers = workers_number - workers_number_for_small_files
    return trembl_workers if trembl_workers > 0 else 1
