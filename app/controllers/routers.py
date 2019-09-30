from app import app
from flask import request
from flask_api import status
from .browsers import Chrome
from .tplinkRouters import TPLinkRouter, TPLinkRouterV2, TPLinkRouterV3

tplink_models = {
    "TL-WR940N": TPLinkRouter,
    "TL-WR941ND": TPLinkRouter,
    "TL-WR740N": TPLinkRouterV2,
    "TL-WR740ND": TPLinkRouterV2,
    "TL-WR541G": TPLinkRouterV3,
    "TL-WR542G": TPLinkRouterV3
}

dlink_models = {}

router_brands = {
    "tplink": tplink_models,
    "tp-link": tplink_models,
    "dlink": dlink_models
}

@app.route('/getMac', methods=['POST'])
def getMac():
    req_data = request.get_json(force=True)
    brand = req_data["router_template"].split(":")[0]
    model = req_data["router_template"].split(":")[1]

    if (not brand in router_brands or
        not model in router_brands[brand]):
        return {
            "success": False,
            "error": "Template not found."
        }, status.HTTP_404_NOT_FOUND
    router_template = router_brands[brand][model]

    router = router_template(req_data['router_ip'], Chrome())
    router.login(req_data['router_login'], req_data['router_password'])
    mac_list = router.getMacList()
    router.logout()
    router.tearDown()
    return mac_list

@app.route('/newMac', methods=['POST'])
def newMac():
    req_data = request.get_json(force=True)
    router = TPLinkRouter(req_data['router_ip'], Chrome())

    router.login(req_data['router_login'], req_data['router_password'])

    return router.newMac(req_data['mac_address'], req_data['mac_description'])

@app.route('/getMacPolicyStatus', methods=['POST'])
def getMacPolicyStatus():
    return {
        "success": False,
        "error": "Not implemented yet."
    }, status.HTTP_501_NOT_IMPLEMENTED

@app.route('/getWifiConfig', methods=['POST'])
def getWifiConfig():
    return {
        "success": False,
        "error": "Not implemented yet."
    }, status.HTTP_501_NOT_IMPLEMENTED

@app.route('/reboot', methods=['POST'])
def reboot():
    return {
        "success": False,
        "error": "Not implemented yet."
    }, status.HTTP_501_NOT_IMPLEMENTED
