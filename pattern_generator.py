import requests
from bs4 import BeautifulSoup


def main():
    url = "https://conwaylife.com/patterns/10enginecordership.cells"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        lines = soup.text.strip().split('\r\n')
        pattern_data = [line for line in lines if not line.startswith('!')]
        output = []
        for index in range(len(pattern_data)):
            data = pattern_data[index]
            for index1 in range(len(data)):
                if data[index1] == "O":
                    output.append((index, index1))
        print(output)
    else:
        print("err")
        print("Status code: {response.status_code}")


if __name__ == "__main__":
    main()
