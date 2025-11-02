from scripts.main import main
from scripts.utils.config import parser
import scripts.utils.config as config
import os
import sys
from dotenv import load_dotenv

if __name__ == "__main__":
    args = parser.parse_args()

    # Загрузка API ключа из .env файла, если он не передан как аргумент
    if not args.api_key:
        dotenv_path = os.path.join(os.path.dirname(__file__), 'scripts', 'secrets.env')
        load_dotenv(dotenv_path=dotenv_path)
        api_key_from_env = os.getenv('NCBI_API_KEY', '')
        # Убедимся, что ключ из .env не равен плейсхолдеру
        if api_key_from_env and api_key_from_env != 'your_key_here':
            args.api_key = api_key_from_env

    # Устанавливаем args в модуле config
    config.args = args

    if not args.email:
        print("Error: the --email argument is required", file=sys.stderr)
        sys.exit(1)

    main()
