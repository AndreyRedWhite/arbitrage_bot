import logging
import subprocess
import re


def check_status() -> bool:
    """
       Checks if a process with the name 'arbitrage_bot.py' is running.

       Returns:
       - bool: True if the process is running, False otherwise.
       """

    try:
        result = subprocess.run('ps -ax | grep arbitrage_bot.py', shell=True, stdout=subprocess.PIPE, text=True)
        processes = result.stdout.split('\n')
        regex = re.compile('[p|P]ython\d? arbitrage_bot\.py')
        for process in processes:
            if regex.search(process):
                return True
        return False
    except Exception as e:
        logging.error(f"An error occured. Here is it:\n{e}")
        return False


def get_last_n_log(n: int, date_only: bool = False) -> str:
    """
       Gets the last n lines from the arbitrage_bot.log file.
       If date_only is True, returns only the date and time from each line.

       Args:
       - n (int): The number of lines to retrieve.
       - date_only (bool): If True, returns only the date and time from each line.

       Returns:
       - str: The last n lines from the log file, or only the date and time from each line if date_only is True.
       """

    try:
        result = subprocess.run(f'tail -n {n} logs/arbitrage_bot.log', shell=True, stdout=subprocess.PIPE, text=True)
        log_lines = result.stdout.strip().split('\n')
        if date_only:
            date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}')
            log_lines = [date_pattern.match(line).group(0) for line in log_lines if date_pattern.match(line)]
        return '\n'.join(log_lines)
    except Exception as e:
        logging.error(f"An error occured. Here is it:\n{e} ")
        return ""


def get_oppotunities(last_lines: int = False):
    """
    Reads the file arbitrage_opportunities.txt and returns its output

    Args:
    - last_lines(int): if set, returns only last n lines from the file

    :return:
    - str: an output from the arbitrage_opportunities.txt file
    """

    try:
        result = subprocess.run('cat arbitrage_opportunities.txt', shell=True, stdout=subprocess.PIPE, text=True)
        opps = result.stdout.strip().split('\n')
        if last_lines:
            lines = [line for line in opps[-last_lines:]]
            return '\n'.join(format_opportunity(line) for line in lines)
        return format_opportunity(opps[-1])
    except Exception as e:
        logging.error(f"An error occurred. Here it is:\n{e}")
        return ""


def format_opportunity(opportunity_str: str) -> str:
    """
    Formats the opportunity string to a more readable format.

    Args:
    - opportunity_str (str): The opportunity string.

    Returns:
    - str: The formatted opportunity string.
    """
    try:
        # Преобразование строки в словарь
        opportunity_dict = eval(opportunity_str.split("! ")[-1])

        # Форматирование строки
        formatted_str = "*Arbitrage Opportunity Found:*\n"
        for key, value in opportunity_dict.items():
            formatted_str += f"*{key.capitalize()}*: `{value}`\n"
        return formatted_str
    except Exception as e:
        logging.error(f"Error formatting opportunity: {e}")
        return opportunity_str


if __name__ == '__main__':
    print(check_status())
    print(get_last_n_log(3, date_only=True))
    print(get_oppotunities(last_lines=2))
