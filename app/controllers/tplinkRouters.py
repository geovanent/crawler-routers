from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import WebDriverException, NoAlertPresentException
from urllib.parse import urlparse
import re
import traceback

def ID(value):
    return By.ID, value

def name(value):
    return By.NAME, value

def css(value):
    return By.CSS_SELECTOR, value

def xpath(value):
    return By.XPATH, value

def link_contains(value):
    return By.PARTIAL_LINK_TEXT, value

class TPLinkBase:
    def __init__(self, URL, driver, mac_separator = "-", activate_status = "enabled", implicitly_wait = 10):
        self.URL = URL
        self.driver = driver
        self.driver.implicitly_wait(implicitly_wait)
        self.mac_separator = mac_separator
        self.wireless_tag_id = 'a7'
        self.mac_filter_tag_id = 'a10'
        self.activate_status = activate_status # String to compare activate status of mac entry
    
    def loginPage(self, login, password):
        '''
        Make login using router with Login Form
        '''
        # Open URL.
        self.driver.get(self.URL)

        # Fill the fields with username and password
        el = self.driver.element
        el(ID('userName')).send_keys(login)
        el(ID('pcPassword')).send_keys(password)
        # Confirm
        el(ID('loginBtn')).click()

    def loginBasicAuth(self, login, password):
        '''
        Make login using router with login basic authentication
        '''
        # Parse URL
        url_parts = urlparse(self.URL)
        # Insert username and password in url to login -> http://user:pass@myrouter.com
        url_parts = url_parts._replace(netloc=str(login) + ":" + str(password) + "@" + url_parts.netloc)
        self.driver.get(url_parts.geturl())

    def format_mac(self, mac: str) -> str:
        '''
        Based on stackoverflow answer
        https://stackoverflow.com/a/29446103
        '''
        mac = re.sub('[.:-]', '', mac).lower()  # remove delimiters and convert to lower case
        mac = ''.join(mac.split())  # remove whitespaces
        hasError = not len(mac) == 12  # length should be now exactly 12 (eg. 008041aefd7e)
        hasError = hasError or not re.match('([0-9a-fA-F]{2}:??){5}([0-9a-fA-F]{2})', mac)

        if hasError:
            return {
                "success": False,
                "error": "Invalid Mac format"
            }
        else:
            return {
                "success": True,
                # convert mac in canonical form (eg. 00:80:41:ae:fd:7e)
                "mac_address": self.mac_separator.join(["%s" % (mac[i:i+2]) for i in range(0, 12, 2)])
            }

    def bottomLeftFrameClick(self, itemID):
        with self.driver.frame('bottomLeftFrame'):
            el = self.driver.element
            el(ID(itemID)).click()
        self.driver.switch_to.default_content()

    def mainFrameClick(self, itemName):
        with self.driver.frame('mainFrame'):
            el = self.driver.find_element_by_name(itemName)
            el.click()
        self.driver.switch_to.default_content()

    def fillMacAndSave(self, mac, descr):
        with self.driver.frame('mainFrame'):
            el = self.driver.find_element_by_name('Mac')
            el.send_keys(mac)
            el = self.driver.find_element_by_name('Desc')
            el.send_keys(descr)
            el = self.driver.find_element_by_name('Save')
            el.click()

    def navigateToWireless(self):
        self.bottomLeftFrameClick(self.wireless_tag_id)

    def navigateToMacFilter(self):
        self.navigateToWireless()
        self.bottomLeftFrameClick(self.mac_filter_tag_id)

    def verifyMacRegistryErrors(self):
        try:
            with self.driver.frame('mainFrame'):
                frame_tables = self.driver.find_element_by_tag_name("table")
                tr_erro = frame_tables.find_elements_by_tag_name("tr")[4]
                assert frame_tables.find_elements_by_tag_name("tr")[0].text.startswith("Erro")
                return {
                    "success": False,
                    "error" : tr_erro.text
                }
        except AssertionError:
            return {
                "success": True,
                "error": ""
            }
        except:
            return {
                "success": False,
                "error": traceback.extract_stack()
            }
        finally:
            self.driver.switch_to.default_content()

    def newMac(self, mac, descr):
        self.navigateToMacFilter()

        formated_mac = self.format_mac(mac)
        if not formated_mac["success"]:
            return formated_mac

        # Click Add button
        self.mainFrameClick('Add')

        # Fill the fields with new Mac
        self.fillMacAndSave(formated_mac["mac_address"], descr)

        try:
            alert_text = Alert(self.driver).text
            Alert(self.driver).accept()
            return {
                "success": False,
                "error": alert_text
            }
        except NoAlertPresentException:
            pass # ok!
        return self.verifyMacRegistryErrors()

    def getMacPolicyStatus(self):
        pass

    def getWifiConfig(self):
        pass

    def changeWifiConfig(self, ssid, password):
        pass

    def reboot(self):
        pass

    def tearDown(self):
        """
        End browser selenium session
        """
        self.driver.stop_client()
        self.driver.close()

    

class TPLinkRouter(TPLinkBase):
    """
    Modelo No. TL-WR940N / TL-WR941ND
    """
    def __init__(self, URL, driver):
        self.URL = URL
        self.driver = driver
        self.mac_separator = "-"
        self.activate_status = "ativado" # String to compare activate status of mac entry
        super().__init__(URL, driver, activate_status=self.activate_status)
    
    def test(self):
        return self.driver.capabilities['browserVersion']

    def login(self, login, password):
        super().loginPage(login, password)
    
    def logout(self):
        self.driver.switch_to.default_content()
        with self.driver.frame('bottomLeftFrame'):
            el = self.driver.element
            el(ID('a53')).click()

    def getMacList(self):
        try:
            super().navigateToMacFilter()
            # Get first page of mac list
            result_list = self.getMacListFromPage()
            # Seek for others pages with mac list
            while(self.nextMacPage()):
                # Concat mac list of the page with result_list
                result_list = result_list + self.getMacListFromPage()
        except:
            return {
                "success": False,
                "error": traceback.extract_stack()
            }
        # self.driver.switch_to.default_content()
        return {
            "success": True,
            "error": "",
            "mac_list": result_list
        }

    def getMacListFromPage(self):
        with self.driver.frame('mainFrame'):
            frame_tables = self.driver.find_element_by_id("autoWidth")
            frame_mac_table = frame_tables.find_elements_by_tag_name("table")[0]
            mac_table = frame_mac_table.find_elements_by_tag_name("tbody")
            mac_list = mac_table[0].find_elements_by_tag_name("tr")
            l_mac = []
            for mac_line in mac_list:
                datas = mac_line.find_elements_by_tag_name("td")
                if(datas[0].text != "ID"): # Ignore header of the mac table
                    l_mac.append({
                        "id": datas[0].text,
                        "mac_address": datas[1].text,
                        "enabled": datas[2].text.lower() == self.activate_status,
                        "description": datas[3].text
                    })
            return l_mac

    def nextMacPage(self):
        try:
            with self.driver.frame('mainFrame'):
                el = self.driver.element
                nextButton = el(name("NextPage"))
                isDisabled = nextButton.get_attribute('disabled')
                if not isDisabled:
                    nextButton.click()
                    return True
        except WebDriverException:
            print("Element is not clickable")
            return False

class TPLinkRouterV2(TPLinkBase):
    """
    Modelo TL-WR740N / TL-WR740ND
    """
    def __init__(self, URL, driver):
        self.URL = URL
        self.driver = driver
        self.mac_separator = "-"
        self.activate_status = "ativado" # String to compare activate status of mac entry
        super().__init__(URL, driver, activate_status=self.activate_status)
    
    def login(self, login, password):
        super().loginBasicAuth(login, password)

    def logout(self):
        super().bottomLeftFrameClick('a53')

    def getMacList(self):
        try:
            super().navigateToMacFilter()
            # Get first page of mac list
            result_list = self.getMacListFromPage()
            # Seek for others pages with mac list
            while(self.nextMacPage()):
                # Concat mac list of the page with result_list
                result_list = result_list + self.getMacListFromPage()
        except:
            return {
                "success": False,
                "error": traceback.extract_stack()
            }    
        self.driver.switch_to.default_content()
        return {
            "success": True,
            "error": "",
            "mac_list": result_list
        }

    def getMacListFromPage(self):
        with self.driver.frame('mainFrame'):
            frame_tables = self.driver.find_element_by_id("autoWidth")
            frame_mac_table = frame_tables.find_elements_by_tag_name("table")[1]
            mac_table = frame_mac_table.find_elements_by_tag_name("tbody")
            mac_list = mac_table[0].find_elements_by_tag_name("tr")
            l_mac = []
            for mac_line in mac_list:
                datas = mac_line.find_elements_by_tag_name("td")
                if(datas[0].text != "ID"): # Ignore header of the mac table
                    l_mac.append({
                        "id": datas[0].text,
                        "mac_address": datas[1].text,
                        "enabled": datas[2].text.lower() == self.activate_status,
                        "description": datas[3].text
                    })
            return l_mac

    def nextMacPage(self):
        try:
            with self.driver.frame('mainFrame'):
                el = self.driver.element
                nextButton = el(name("NextPage"))
                isDisabled = nextButton.get_attribute('disabled')
                if not isDisabled:
                    nextButton.click()
                    return True
        except WebDriverException:
            return False

class TPLinkRouterV3(TPLinkBase):
    """
    Modelo TL-WR541G / TL-WR542G
    """
    def __init__(self, URL, driver):
        self.URL = URL
        self.driver = driver
        self.mac_separator = "-"
        self.activate_status = "Enabled".lower() # String to compare activate status of mac entry (must be in lower case)
        super().__init__(URL, driver, activate_status=self.activate_status, implicitly_wait=5)
        self.mac_filter_tag_id = 'a9'
    
    def login(self, login, password):
        super().loginBasicAuth(login, password)

    def logout(self):
        pass

    def getMacList(self):
        try:
            super().navigateToMacFilter()
            # Get first page of mac list
            result_list = self.getMacListFromPage()
            # Seek for others pages with mac list
            while(self.nextMacPage()):
                # Concat mac list of the page with result_list
                result_list = result_list + self.getMacListFromPage()
        except:
            return {
                "success": False,
                "error": traceback.extract_stack()
            }    
        self.driver.switch_to.default_content()
        return {
            "success": True,
            "error": "",
            "mac_list": result_list
        }

    def getMacListFromPage(self):
        with self.driver.frame('mainFrame'):
            frame_tables = self.driver.find_element_by_id("autoWidth")
            frame_mac_table = frame_tables.find_elements_by_tag_name("table")[0]
            mac_table = frame_mac_table.find_elements_by_tag_name("tbody")
            mac_list = mac_table[0].find_elements_by_tag_name("tr")
            l_mac = []
            for mac_line in mac_list:
                datas = mac_line.find_elements_by_tag_name("td")
                if(datas[0].text != "ID"): # Ignore header of the mac table
                    l_mac.append({
                        "id": datas[0].text,
                        "mac_address": datas[1].text,
                        "enabled": datas[2].text.lower() == self.activate_status,
                        "description": datas[4].text
                    })
            return l_mac

    def nextMacPage(self):
        try:
            with self.driver.frame('mainFrame'):
                el = self.driver.element
                nextButton = el(name("Next"))
                isDisabled = nextButton.get_attribute('disabled')
                if not isDisabled:
                    nextButton.click()
                    return True
        except WebDriverException:
            return False
