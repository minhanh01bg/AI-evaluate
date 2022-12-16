import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='Your name')
    args = parser.parse_args()
    print('Hello, {}'.format(args.name))

if __name__ == '__main__':
    main()
    
