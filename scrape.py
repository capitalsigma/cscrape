import re
import mechanize
import bs4
import sys
import cookielib


class CustomBrowser(mechanize.Browser):
    """ Customized mechanize.Browser class for scraping the UChicago people
    directory """    

    def __init__(self, outFilePath):
        """ Set a cookie jar, add Firefox headers """
        mechanize.Browser.__init__(self)
        self.cookiejar = cookielib.LWPCookieJar()
        self.set_cookiejar(self.cookiejar)
        self.addheaders = self.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
        self.isFirstSearch = 1
        self.outFile = open(outFilePath, "a") 
        

    def login(self, username, password):
        """ Login through Shibboleth """
        url = "https://directory.uchicago.edu/return_after_login"

        self.open(url)

        # Actual sign in
        self.select_form(nr=0)
        self.form["j_username"] = username
        self.form["j_password"] = password
        self.submit()

        # Click through
        self.select_form(nr=0)
        self.submit()

        if verbosity:
            print "Successfully logged in"
    
    def first_search(self):
        """ Once logged in, start up a search for names matching * """
        self.select_form(nr = 0)
        self.form["name"] = "*"
        self.submit()
        self.isFirstSearch = 0
        
        if verbosity:
            print "Performed first search"

    def next_page(self):
        """ Go to the next page. Return true if there is another page, false otherwise """
        try:
            link = self.links(text_regex = "Next").next()
        except StopIteration:
            if verbosity:
                print "On final page"
            return False

        self.follow_link(link)
        if verbosity:
            print "Advanced to the next page"
        return True

    def advance(self):
        """ Wrapper for first_search and next_page """
        if self.isFirstSearch:
            self.first_search()
            return True
        else:
            return self.next_page()

    def scrape_cnets(self):
        """ Return a list of the cnets on a given page """
        ret = []
        soup = bs4.BeautifulSoup(self.response().read())
        
        for email in soup.find_all(href=re.compile("mailto.*")):
            ret.append(email.string.split("@")[0])

        if verbosity:
            print "Scraped {} cnets".format(len(ret))

        return ret

    def write_to_file(self, cnets):
        """ Given a list of cnets and the path to a file """ 
        for cnet in cnets:
            self.outFile.write(cnet + "\n")
        if verbosity:
            print "Wrote {} cnets".format(len(cnets))
            
    def main(self, username, password):
        self.login(username, password)

        while self.advance():
            cnets = self.scrape_cnets()
            self.write_to_file(cnets)
        


# Non-class functions to process commandline input
def proc_args():
    global verbosity
    if len(sys.argv) > 4:
        verbosity = bool(sys.argv[4])
    return len(sys.argv) < 4 or \
        (sys.argv[1] == "-h") or \
        (sys.argv[1] == "--help") 

verbosity = False
def main(argv):
    if proc_args():
        str = \
        "Usage: {} username password path_to_output_file [verbose?]".format(sys.argv[0])
        print str
        sys.exit(0)
    else:
        cB = CustomBrowser(argv[3])
        cB.main(argv[1], argv[2])
        sys.exit(0)


main(sys.argv)
