#!/usr/bin/env python
#coding:utf-8
import sys,os
from bottle import Bottle
from bottle import request
from bottle import response
from bottle import redirect
from bottle import MakoTemplate
from bottle import static_file
from bottle import abort
from bottle import mako_template as render
from libs.paginator import Paginator
from libs import utils
from libs.radius_attrs import radius_attrs
from hashlib import md5
from websock import websock
import bottle
import models
import forms
import datetime
import json
from base import *


app = Bottle()

###############################################################################
# Basic handle         
###############################################################################

@app.route('/',apply=auth_opr)
def index(db):    
    online_count = db.query(models.SlcRadOnline.id).count()
    user_total = db.query(models.SlcRadAccount.account_number).filter_by(status=1).count()
    return render("index",**locals())

@app.error(403)
def error404(error):
    return render("error.html",msg=u"非授权的访问")
    
@app.error(404)
def error404(error):
    return render("error.html",msg=u"页面不存在 - 请联系管理员!")

@app.error(500)
def error500(error):
    return render("error.html",msg=u"出错了： %s"%error.exception)

@app.route('/static/:path#.+#')
def route_static(path):
    return static_file(path, root='./static')

###############################################################################
# login handle         
###############################################################################

@app.get('/login')
def admin_login_get(db):
    return render("login")

@app.post('/login')
def admin_login_post(db):
    uname = request.forms.get("username")
    upass = request.forms.get("password")
    if not uname:return dict(code=1,msg=u"请填写用户名")
    if not upass:return dict(code=1,msg=u"请填写密码")
    enpasswd = md5(upass.encode()).hexdigest()
    opr = db.query(models.SlcOperator).filter_by(
        operator_name=uname,
        operator_pass=enpasswd
    ).first()
    if not opr:return dict(code=1,msg=u"用户名密码不符")
    if opr.operator_status == 1:return dict(code=1,msg=u"该操作员账号已被停用")
    set_cookie('username',uname)
    set_cookie('opr_type',opr.operator_type)
    set_cookie('login_time', utils.get_currtime())
    set_cookie('login_ip', request.remote_addr)  
    
    if opr.operator_type > 0:
        permit.unbind_opr(uname)
        for rule in db.query(models.SlcOperatorRule).filter_by(operator_name=uname):
            permit.bind_opr(rule.operator_name,rule.rule_path)  

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = uname
    ops_log.operate_ip = request.remote_addr
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)登陆'%(uname,)
    db.add(ops_log)
    db.commit()

    return dict(code=0,msg="ok")

@app.get("/logout")
def admin_logout(db):
    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)登出'%(get_cookie("username"),)
    db.add(ops_log)    
    db.commit()
    if get_cookie('opt_type') > 0:
        permit.unbind_opr(get_cookie("username"))
    set_cookie('username',None)
    set_cookie('login_time', None)
    set_cookie('opr_type',None)
    set_cookie('login_ip', None)   
    request.cookies.clear()
    redirect('/login')

###############################################################################
# param config      
############################################################################### 

@app.get('/param',apply=auth_opr)
def param(db):   
    return render("base_form",form=forms.param_form(db.query(models.SlcParam)))

@app.post('/param',apply=auth_opr)
def param_update(db): 
    params = db.query(models.SlcParam)
    wsflag = False
    for param in params:
        if param.param_name in request.forms:
            _value = request.forms.get(param.param_name)
            if _value: _value = _value.decode('utf-8')
            if _value and param.param_value not in _value:
                param.param_value = _value
            if param.param_name == '3_radiusd_address':
                if param.param_value != MakoTemplate.defaults['radaddr']:
                    MakoTemplate.defaults['radaddr'] = param.param_value
                    wsflag = True
            if param.param_name == '4_radiusd_admin_port':
                if param.param_value != MakoTemplate.defaults['adminport']:
                    MakoTemplate.defaults['adminport'] = param.param_value
                    wsflag = True     
            if param.param_name == u'reject_delay':
                websock.update_cache("reject_delay",reject_delay=param.param_value)       
                
    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改参数:%s'%(
        get_cookie("username"),
        json.dumps(','.join([ serial_json(param) for p in params ]),ensure_ascii=False)
    )
    db.add(ops_log)
    db.commit()
    
    if wsflag:
        websock.reconnect(
            MakoTemplate.defaults['radaddr'],
            MakoTemplate.defaults['adminport'],
        )
        
    websock.update_cache("param")
    redirect("/param")
    
permit.add_route("/param",u"系统参数管理",u"系统管理",is_menu=True,order=0)

###############################################################################
# password update     
###############################################################################

@app.get('/passwd',apply=auth_opr)
def passwd(db):   
    form=forms.passwd_update_form()
    form.fill(operator_name=get_cookie("username"))
    return render("base_form",form=form)

@app.post('/passwd',apply=auth_opr)
def passwd_update(db):  
    form=forms.passwd_update_form() 
    if not form.validates(source=request.forms):
        return render("base_form", form=form)
    if form.d.operator_pass != form.d.operator_pass_chk:
        return render("base_form", form=form,msg=u"确认密码不一致")
    opr = db.query(models.SlcOperator).first()
    opr.operator_pass = md5(form.d.operator_pass).hexdigest()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改密码'%(get_cookie("username"),)
    db.add(ops_log)

    db.commit()
    redirect("/passwd")

###############################################################################
# node manage   
###############################################################################

@app.get('/node',apply=auth_opr)
def node(db):   
    return render("sys_node_list", page_data = get_page_data(db.query(models.SlcNode)))
    
permit.add_route("/node",u"区域信息管理",u"系统管理",is_menu=True,order=1)    

@app.get('/node/add',apply=auth_opr)
def node_add(db):  
    return render("base_form",form=forms.node_add_form())

@app.post('/node/add',apply=auth_opr)
def node_add_post(db): 
    form=forms.node_add_form()
    if not form.validates(source=request.forms):
        return render("base_form", form=form)
    node = models.SlcNode()
    node.node_name = form.d.node_name
    node.node_desc = form.d.node_desc
    db.add(node)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)新增区域信息:%s'%(get_cookie("username"),serial_json(node))
    db.add(ops_log)

    db.commit()
    redirect("/node")
    
permit.add_route("/node/add",u"新增区域",u"系统管理",order=1.01)

@app.get('/node/update',apply=auth_opr)
def node_update(db):  
    node_id = request.params.get("node_id")
    form=forms.node_update_form()
    form.fill(db.query(models.SlcNode).get(node_id))
    return render("base_form",form=form)

@app.post('/node/update',apply=auth_opr)
def node_add_update(db): 
    form=forms.node_update_form()
    if not form.validates(source=request.forms):
        return render("base_form", form=form)
    node = db.query(models.SlcNode).get(form.d.id)
    node.node_name = form.d.node_name
    node.node_desc = form.d.node_desc

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改区域信息:%s'%(get_cookie("username"),serial_json(node))
    db.add(ops_log)

    db.commit()
    redirect("/node")    
    
permit.add_route("/node/update",u"修改区域",u"系统管理",order=1.02)

@app.get('/node/delete',apply=auth_opr)
def node_delete(db):     
    node_id = request.params.get("node_id")
    if db.query(models.SlcMember.member_id).filter_by(node_id=node_id).count()>0:
        return render("error",msg=u"该节点下有用户，不允许删除")
    db.query(models.SlcNode).filter_by(id=node_id).delete()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)删除区域信息:%s'%(get_cookie("username"),node_id)
    db.add(ops_log)

    db.commit() 
    redirect("/node")  
    
permit.add_route("/node/delete",u"删除区域",u"系统管理",order=1.03)

###############################################################################
# bas manage    
###############################################################################

@app.route('/bas',apply=auth_opr,method=['GET','POST'])
def bas(db):   
    return render("sys_bas_list", 
        bastype = forms.bastype,
        bas_list = db.query(models.SlcRadBas))
        
permit.add_route("/bas",u"BAS信息管理",u"系统管理",is_menu=True,order=2)
    
@app.get('/bas/add',apply=auth_opr)
def bas_add(db):  
    return render("base_form",form=forms.bas_add_form())

@app.post('/bas/add',apply=auth_opr)
def bas_add_post(db): 
    form=forms.bas_add_form()
    if not form.validates(source=request.forms):
        return render("base_form", form=form)
    if db.query(models.SlcRadBas.id).filter_by(ip_addr=form.d.ip_addr).count()>0:
        return render("base_form", form=form,msg=u"Bas地址已经存在")        
    bas = models.SlcRadBas()
    bas.ip_addr = form.d.ip_addr
    bas.bas_name = form.d.bas_name
    bas.time_type = form.d.time_type
    bas.vendor_id = form.d.vendor_id
    bas.bas_secret = form.d.bas_secret
    bas.coa_port = form.d.coa_port
    db.add(bas)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)新增BAS信息:%s'%(get_cookie("username"),serial_json(bas))
    db.add(ops_log)

    db.commit()
    redirect("/bas")
    
permit.add_route("/bas/add",u"新增BAS",u"系统管理",order=2.01)

@app.get('/bas/update',apply=auth_opr)
def bas_update(db):  
    bas_id = request.params.get("bas_id")
    form=forms.bas_update_form()
    form.fill(db.query(models.SlcRadBas).get(bas_id))
    return render("base_form",form=form)

@app.post('/bas/update',apply=auth_opr)
def bas_add_update(db): 
    form=forms.bas_update_form()
    if not form.validates(source=request.forms):
        return render("base_form", form=form)
    bas = db.query(models.SlcRadBas).get(form.d.id)
    bas.bas_name = form.d.bas_name
    bas.time_type = form.d.time_type
    bas.vendor_id = form.d.vendor_id
    bas.bas_secret = form.d.bas_secret
    bas.coa_port = form.d.coa_port

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改BAS信息:%s'%(get_cookie("username"),serial_json(bas))
    db.add(ops_log)

    db.commit()
    websock.update_cache("bas",ip_addr=bas.ip_addr)
    redirect("/bas")    
    
permit.add_route("/bas/update",u"修改BAS",u"系统管理",order=2.02)

@app.get('/bas/delete',apply=auth_opr)
def bas_delete(db):     
    bas_id = request.params.get("bas_id")
    db.query(models.SlcRadBas).filter_by(id=bas_id).delete()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)删除BAS信息:%s'%(get_cookie("username"),bas_id)
    db.add(ops_log)

    db.commit() 
    redirect("/bas")    

permit.add_route("/bas/delete",u"删除BAS",u"系统管理",order=2.03)


###############################################################################
# opr manage    
###############################################################################

@app.route('/opr',apply=auth_opr,method=['GET','POST'])
def opr(db):   
    return render("sys_opr_list", 
        oprtype = forms.opr_type,
        oprstatus = forms.opr_status_dict,
        opr_list = db.query(models.SlcOperator))
        
permit.add_route("/opr",u"操作员管理",u"系统管理",is_menu=True,order=3)
    
@app.get('/opr/add',apply=auth_opr)
def opr_add(db):  
    return render("sys_opr_form",form=forms.opr_add_form(),rules=[])

@app.post('/opr/add',apply=auth_opr)
def opr_add_post(db): 
    form=forms.opr_add_form()
    if not form.validates(source=request.forms):
        return render("sys_opr_form", form=form)
    if db.query(models.SlcOperator.id).filter_by(operator_name=form.d.operator_name).count()>0:
        return render("sys_opr_form", form=form,msg=u"操作员已经存在")   
        
    opr = models.SlcOperator()
    opr.operator_name = form.d.operator_name
    opr.operator_type = 1
    opr.operator_pass = md5(form.d.operator_pass).hexdigest()
    opr.operator_desc = form.d.operator_desc
    opr.operator_status = form.d.operator_status
    db.add(opr)
    
    for path in request.params.getall("rule_item"):
        item = permit.get_route(path)
        if not item:continue
        rule = models.SlcOperatorRule()
        rule.operator_name = opr.operator_name
        rule.rule_name = item['name']
        rule.rule_path = item['path']
        rule.rule_category = item['category']
        db.add(rule)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)新增操作员信息:%s'%(get_cookie("username"),serial_json(opr))
    db.add(ops_log)

    db.commit()
    redirect("/opr")
    
permit.add_route("/opr/add",u"新增操作员",u"系统管理",order=3.01)

@app.get('/opr/update',apply=auth_opr)
def opr_update(db):  
    opr_id = request.params.get("opr_id")
    opr = db.query(models.SlcOperator).get(opr_id)
    form=forms.opr_update_form()
    form.fill(opr)
    form.operator_pass.set_value('')
    rules = db.query(models.SlcOperatorRule.rule_path).filter_by(operator_name=opr.operator_name)
    rules = [r[0] for r in rules]
    return render("sys_opr_form",form=form,rules=rules)

@app.post('/opr/update',apply=auth_opr)
def opr_add_update(db): 
    form=forms.opr_update_form()
    if not form.validates(source=request.forms):
        return render("sys_opr_form", form=form)
    opr = db.query(models.SlcOperator).get(form.d.id)
    
    if form.d.operator_pass:
        opr.operator_pass = md5(form.d.operator_pass).hexdigest()
    opr.operator_desc = form.d.operator_desc
    opr.operator_status = form.d.operator_status
    
    # update rules
    db.query(models.SlcOperatorRule).filter_by(operator_name=opr.operator_name).delete()
    
    for path in request.params.getall("rule_item"):
        item = permit.get_route(path)
        if not item:continue
        rule = models.SlcOperatorRule()
        rule.operator_name = opr.operator_name
        rule.rule_name = item['name']
        rule.rule_path = item['path']
        rule.rule_category = item['category']
        db.add(rule)
        
    permit.unbind_opr(opr.operator_name)
    for rule in db.query(models.SlcOperatorRule).filter_by(operator_name=opr.operator_name):
        permit.bind_opr(rule.operator_name,rule.rule_path)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改操作员信息:%s'%(get_cookie("username"),serial_json(opr))
    db.add(ops_log)

    db.commit()
    redirect("/opr")    
    
permit.add_route("/opr/update",u"修改操作员",u"系统管理",order=3.02)

@app.get('/opr/delete',apply=auth_opr)
def opr_delete(db):     
    opr_id = request.params.get("opr_id")
    db.query(models.SlcOperator).filter_by(id=opr_id).delete()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)删除操作员信息:%s'%(get_cookie("username"),opr_id)
    db.add(ops_log)

    db.commit() 
    redirect("/opr")    

permit.add_route("/opr/delete",u"删除操作员",u"系统管理",order=3.03)

###############################################################################
# product manage       
###############################################################################

@app.route('/product',apply=auth_opr,method=['GET','POST'])
def product(db):   
    _query = db.query(models.SlcRadProduct)
    return render("sys_product_list", 
        node_list=db.query(models.SlcNode),
        page_data = get_page_data(_query))
        
@app.get('/product/detail',apply=auth_opr)
def product_detail(db):
    product_id = request.params.get("product_id")   
    product = db.query(models.SlcRadProduct).get(product_id)
    if not product:
        return render("error",msg=u"资费不存在")
    product_attrs = db.query(models.SlcRadProductAttr).filter_by(product_id=product_id)
    return render("sys_product_detail",product=product,product_attrs=product_attrs) 

permit.add_route("/product",u"资费信息管理",u"系统管理",is_menu=True,order=4)
permit.add_route("/product/detail",u"资费详情查看",u"系统管理",order=4.01)

@app.get('/product/add',apply=auth_opr)
def product_add(db):  
    return render("sys_product_form",form=forms.product_add_form())
    
@app.post('/product/add',apply=auth_opr)
def product_add_post(db): 
    form=forms.product_add_form()
    if not form.validates(source=request.forms):
        return render("sys_product_form", form=form)      
    product = models.SlcRadProduct()
    product.product_name = form.d.product_name
    product.product_policy = form.d.product_policy
    product.product_status = form.d.product_status
    product.fee_months = form.d.get("fee_months",0)
    product.bind_mac = form.d.bind_mac
    product.bind_vlan = form.d.bind_vlan
    product.concur_number = form.d.concur_number
    product.fee_period = form.d.fee_period
    product.fee_price = utils.yuan2fen(form.d.fee_price)
    product.input_max_limit = form.d.input_max_limit
    product.output_max_limit = form.d.output_max_limit
    _datetime = datetime.datetime.now().strftime( "%Y-%m-%d %H:%M:%S")
    product.create_time = _datetime
    product.update_time = _datetime
    db.add(product)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)新增资费信息:%s'%(get_cookie("username"),serial_json(product))
    db.add(ops_log)

    db.commit()
    redirect("/product")
    
permit.add_route("/product/add",u"新增资费",u"系统管理",order=4.02)

@app.get('/product/update',apply=auth_opr)
def product_update(db):  
    product_id = request.params.get("product_id")
    form=forms.product_update_form()
    product = db.query(models.SlcRadProduct).get(product_id)
    form.fill(product)
    form.product_policy_name.set_value(forms.product_policy[product.product_policy])
    form.fee_price.set_value(utils.fen2yuan(product.fee_price))
    return render("sys_product_form",form=form)

@app.post('/product/update',apply=auth_opr)
def product_update(db): 
    form=forms.product_update_form()
    if not form.validates(source=request.forms):
        return render("sys_product_form", form=form)
    product = db.query(models.SlcRadProduct).get(form.d.id)
    product.product_name = form.d.product_name
    product.product_status = form.d.product_status
    product.fee_months = form.d.get("fee_months",0)
    product.bind_mac = form.d.bind_mac
    product.bind_vlan = form.d.bind_vlan
    product.concur_number = form.d.concur_number
    product.fee_period = form.d.fee_period
    product.fee_price = utils.yuan2fen(form.d.fee_price)
    product.input_max_limit = form.d.input_max_limit
    product.output_max_limit = form.d.output_max_limit
    product.update_time = utils.get_currtime()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改资费信息:%s'%(get_cookie("username"),serial_json(product))
    db.add(ops_log)

    db.commit()
    websock.update_cache("product",product_id=product.id)
    redirect("/product")    
    
permit.add_route("/product/update",u"修改资费",u"系统管理",order=4.03)    

@app.get('/product/delete',apply=auth_opr)
def product_delete(db):     
    product_id = request.params.get("product_id")
    if db.query(models.SlcRadAccount).filter_by(product_id=product_id).count()>0:
        return render("error",msg=u"该套餐有用户使用，不允许删除") 
    db.query(models.SlcRadProduct).filter_by(id=product_id).delete()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)删除资费信息:%s'%(get_cookie("username"),product_id)
    db.add(ops_log)

    db.commit() 
    websock.update_cache("product",product_id=product_id)
    redirect("/product")   
    
permit.add_route("/product/delete",u"删除资费",u"系统管理",order=4.04)

@app.get('/product/attr/add',apply=auth_opr)
def product_attr_add(db): 
    product_id = request.params.get("product_id")
    if db.query(models.SlcRadProduct).filter_by(id=product_id).count()<=0:
        return render("error",msg=u"资费不存在") 
    form = forms.product_attr_add_form()
    form.product_id.set_value(product_id)
    return render("sys_pattr_form",form=form,pattrs=radius_attrs)

@app.post('/product/attr/add',apply=auth_opr)
def product_attr_add(db): 
    form = forms.product_attr_add_form()
    if not form.validates(source=request.forms):
        return render("sys_pattr_form", form=form,pattrs=radius_attrs)   
    attr = models.SlcRadProductAttr()
    attr.product_id = form.d.product_id
    attr.attr_name = form.d.attr_name
    attr.attr_value = form.d.attr_value
    attr.attr_desc = form.d.attr_desc
    db.add(attr)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)新增资费属性信息:%s'%(get_cookie("username"),serial_json(attr))
    db.add(ops_log)

    db.commit()

    redirect("/product/detail?product_id="+form.d.product_id) 
    
permit.add_route("/product/attr/add",u"新增资费扩展属性",u"系统管理",order=4.05)

@app.get('/product/attr/update',apply=auth_opr)
def product_attr_update(db): 
    attr_id = request.params.get("attr_id")
    attr = db.query(models.SlcRadProductAttr).get(attr_id)
    form = forms.product_attr_update_form()
    form.fill(attr)
    return render("sys_pattr_form",form=form,pattrs=radius_attrs)

@app.post('/product/attr/update',apply=auth_opr)
def product_attr_update(db): 
    form = forms.product_attr_update_form()
    if not form.validates(source=request.forms):
        return render("pattr_form", form=form,pattrs=radius_attrs)   
    attr = db.query(models.SlcRadProductAttr).get(form.d.id)
    attr.attr_name = form.d.attr_name
    attr.attr_value = form.d.attr_value
    attr.attr_desc = form.d.attr_desc

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改资费属性信息:%s'%(get_cookie("username"),serial_json(attr))
    db.add(ops_log)

    db.commit()
    websock.update_cache("product",product_id=form.d.product_id)
    redirect("/product/detail?product_id="+form.d.product_id) 
    
permit.add_route("/product/attr/update",u"修改资费扩展属性",u"系统管理",order=4.06)

@app.get('/product/attr/delete',apply=auth_opr)
def product_attr_update(db): 
    attr_id = request.params.get("attr_id")
    attr = db.query(models.SlcRadProductAttr).get(attr_id)
    product_id = attr.product_id
    db.query(models.SlcRadProductAttr).filter_by(id=attr_id).delete()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)删除资费属性信息:%s'%(get_cookie("username"),serial_json(attr))
    db.add(ops_log)

    db.commit()
    websock.update_cache("product",product_id=product_id)
    redirect("/product/detail?product_id=%s"%product_id)     
    
permit.add_route("/product/attr/delete",u"删除资费扩展属性",u"系统管理",order=4.07)

###############################################################################
# group manage      
###############################################################################

@app.route('/group',apply=auth_opr,method=['GET','POST'])
def group(db):   
    _query = db.query(models.SlcRadGroup)
    return render("sys_group_list", 
        page_data = get_page_data(_query))

permit.add_route("/group",u"用户组管理",u"系统管理",is_menu=True,order=5)
   
@app.get('/group/add',apply=auth_opr)
def group_add(db):  
    return render("base_form",form=forms.group_add_form())

@app.post('/group/add',apply=auth_opr)
def group_add_post(db): 
    form=forms.group_add_form()
    if not form.validates(source=request.forms):
        return render("base_form", form=form)    
    group = models.SlcRadGroup()
    group.group_name = form.d.group_name
    group.group_desc = form.d.group_desc
    group.bind_mac = form.d.bind_mac
    group.bind_vlan = form.d.bind_vlan
    group.concur_number = form.d.concur_number
    group.update_time = utils.get_currtime()
    db.add(group)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)新增用户组信息:%s'%(get_cookie("username"),serial_json(group))
    db.add(ops_log)

    db.commit()
    redirect("/group")
    
permit.add_route("/group/add",u"新增用户组",u"系统管理",order=5.01)

@app.get('/group/update',apply=auth_opr)
def group_update(db):  
    group_id = request.params.get("group_id")
    form=forms.group_update_form()
    form.fill(db.query(models.SlcRadGroup).get(group_id))
    return render("base_form",form=form)

@app.post('/group/update',apply=auth_opr)
def group_add_update(db): 
    form=forms.group_update_form()
    if not form.validates(source=request.forms):
        return render("base_form", form=form)
    group = db.query(models.SlcRadGroup).get(form.d.id)
    group.group_name = form.d.group_name
    group.group_desc = form.d.group_desc
    group.bind_mac = form.d.bind_mac
    group.bind_vlan = form.d.bind_vlan
    group.concur_number = form.d.concur_number
    group.update_time = utils.get_currtime()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改用户组信息:%s'%(get_cookie("username"),serial_json(group))
    db.add(ops_log)

    db.commit()
    websock.update_cache("group",group_id=group.id)
    redirect("/group")    
    
permit.add_route("/group/update",u"修改用户组",u"系统管理",order=5.02)

@app.get('/group/delete',apply=auth_opr)
def group_delete(db):     
    group_id = request.params.get("group_id")
    db.query(models.SlcRadGroup).filter_by(id=group_id).delete()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)删除用户组信息:%s'%(get_cookie("username"),group_id)
    db.add(ops_log)

    db.commit() 
    websock.update_cache("group",group_id=group_id)
    redirect("/group")    
    
permit.add_route("/group/delete",u"删除用户组",u"系统管理",order=5.03)

###############################################################################
# roster manage    
###############################################################################

@app.route('/roster',apply=auth_opr,method=['GET','POST'])
def roster(db):   
    _query = db.query(models.SlcRadRoster)
    return render("sys_roster_list", 
        page_data = get_page_data(_query))
        
permit.add_route("/roster",u"黑白名单管理",u"系统管理",is_menu=True,order=6)

@app.get('/roster/add',apply=auth_opr)
def roster_add(db):  
    return render("sys_roster_form",form=forms.roster_add_form())

@app.post('/roster/add',apply=auth_opr)
def roster_add_post(db): 
    form=forms.roster_add_form()
    if not form.validates(source=request.forms):
        return render("sys_roster_form", form=form)  
    if db.query(models.SlcRadRoster.id).filter_by(mac_addr=form.d.mac_addr).count()>0:
        return render("sys_roster_form", form=form,msg=u"MAC地址已经存在")     
    roster = models.SlcRadRoster()
    roster.mac_addr = form.d.mac_addr.replace("-",":").upper()
    roster.begin_time = form.d.begin_time
    roster.end_time = form.d.end_time
    roster.roster_type = form.d.roster_type
    db.add(roster)

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)新增黑白名单信息:%s'%(get_cookie("username"),serial_json(roster))
    db.add(ops_log)

    db.commit()
    websock.update_cache("roster",mac_addr=roster.mac_addr)
    redirect("/roster")
    
permit.add_route("/roster/add",u"新增黑白名单",u"系统管理",order=6.01)    

@app.get('/roster/update',apply=auth_opr)
def roster_update(db):  
    roster_id = request.params.get("roster_id")
    form=forms.roster_update_form()
    form.fill(db.query(models.SlcRadRoster).get(roster_id))
    return render("sys_roster_form",form=form)

@app.post('/roster/update',apply=auth_opr)
def roster_add_update(db): 
    form=forms.roster_update_form()
    if not form.validates(source=request.forms):
        return render("sys_roster_form", form=form)       
    roster = db.query(models.SlcRadRoster).get(form.d.id)
    roster.begin_time = form.d.begin_time
    roster.end_time = form.d.end_time
    roster.roster_type = form.d.roster_type

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)修改黑白名单信息:%s'%(get_cookie("username"),serial_json(roster))
    db.add(ops_log)

    db.commit()
    websock.update_cache("roster",mac_addr=roster.mac_addr)
    redirect("/roster")    
    
permit.add_route("/roster/update",u"修改白黑名单",u"系统管理",order=6.02)    

@app.get('/roster/delete',apply=auth_opr)
def roster_delete(db):     
    roster_id = request.params.get("roster_id")
    mac_addr = db.query(models.SlcRadRoster).get(roster_id).mac_addr
    db.query(models.SlcRadRoster).filter_by(id=roster_id).delete()

    ops_log = models.SlcRadOperateLog()
    ops_log.operator_name = get_cookie("username")
    ops_log.operate_ip = get_cookie("login_ip")
    ops_log.operate_time = utils.get_currtime()
    ops_log.operate_desc = u'操作员(%s)删除黑白名单信息:%s'%(get_cookie("username"),roster_id)
    db.add(ops_log)

    db.commit() 
    websock.update_cache("roster",mac_addr=mac_addr)
    redirect("/roster")        

permit.add_route("/roster/delete",u"删除黑白名单",u"系统管理",order=6.03)
