import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('string',metavar='Name', help='Your name',type=str, nargs='?', default='Minh anh')
    parser.add_argument('--name',action="store_true", default='Minh anh', help='Your name')
    args = parser.parse_args()
    print('Hello, {}'.format(args.name))

if __name__ == '__main__':
    main()
    
