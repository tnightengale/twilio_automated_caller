# twilio_automated_caller
An autodialer for student painting company to automatically navigate the company website, and make VoIP calls to leads.


## Steps to use program:
**Note you must be affiliated with Student Works painting and have a login for their portal, SIMON**

1. Create virtual enviroment and install requirements.txt
2. Visit the forked Twilio VoIP repo: https://github.com/tnightengale/client-quickstart-python and follow the set-up instructions
  - You will also need to create a paid twilio account as part of this process.
  - Once you have the 4 credentials laidout in the README.md of the Twilio VoIP repo, ensure that you run the command `$ cp .env.example .env` to create a copy of the `.env.example` credential file. Then run `$ open -a TextEdit .env` and replace the values `.env ` with your credentials. Continue following the Twilio VoIP README.md setup instructions. 
3. Save your SIMON credentials as enviroment variables from the bash line as follows:
  - `$ export SIMON_email=your_email` and `$ export SIMON_pass=your_password`
4. Note the path of your chrome driver .exe file and replace the set path in the auto_caller.py file
5. Run `$ python auto_caller.py`
