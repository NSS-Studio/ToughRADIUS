package org.toughradius.entity;

import org.toughradius.common.DateTimeUtil;
import org.toughradius.common.ValidateUtil;

import java.math.BigDecimal;
import java.math.BigInteger;

public class SubscribeForm {

    private Integer id;

    private Integer nodeId;

    private Integer areaId;

    private Integer productId;

    private String subscriber;

    private String realname;

    private String password;

    private String billType;

    private String domain;

    private String addrPool;

    private String policy;

    private Integer activeNum;

    private Integer isOnline;

    private BigInteger flowAmount;

    private Boolean bindMac;

    private Boolean bindVlan;

    private String ipAddr;

    private String macAddr;

    private Integer inVlan;

    private Integer outVlan;

    private BigDecimal upRate;

    private BigDecimal downRate;

    private BigDecimal upPeakRate;

    private BigDecimal downPeakRate;

    private String upRateCode;

    private String downRateCode;

    private String status;

    private String beginTime;

    private String expireTime;

    private String createTime;

    private String updateTime;

    private String remark;

    public Subscribe getSubscribeData(){
        Subscribe subs = new Subscribe();
        subs.setId(getId());
        subs.setSubscriber(getSubscriber());
        subs.setRealname(getRealname());
        subs.setActiveNum(getActiveNum());
        subs.setAddrPool(getAddrPool());
        subs.setAreaId(getAreaId());
        if(ValidateUtil.isNotEmpty(getBeginTime()) && getBeginTime().length() == 16)
            subs.setBeginTime(DateTimeUtil.toTimestamp(getBeginTime()+":00"));
        if(ValidateUtil.isNotEmpty(getExpireTime()) && getExpireTime().length() == 16)
            subs.setExpireTime(DateTimeUtil.toTimestamp(getExpireTime()+":00"));
        subs.setUpdateTime(DateTimeUtil.nowTimestamp());
        subs.setBillType(getBillType());
        subs.setBindMac(getBindMac());
        subs.setBindVlan(getBindVlan());
        subs.setDomain(getDomain());
        subs.setIpAddr(getIpAddr());
        subs.setFlowAmount(getFlowAmount());
        subs.setMacAddr(getMacAddr());
        subs.setInVlan(getInVlan());
        subs.setOutVlan(getOutVlan());
        subs.setUpRate(getUpRate());
        subs.setDownRate(getDownRate());
        subs.setUpPeakRate(getUpPeakRate());
        subs.setDownPeakRate(getDownPeakRate());
        subs.setUpRateCode(getUpRateCode());
        subs.setDownRateCode(getDownRateCode());
        subs.setPolicy(getPolicy());
        subs.setRealname(getRealname());
        subs.setNodeId(getNodeId());
        subs.setPassword(getPassword());
        subs.setProductId(getProductId());
        return subs;
    }

    public Integer getId() {
        return id;
    }

    public void setId(Integer id) {
        this.id = id;
    }

    public Integer getNodeId() {
        return nodeId;
    }

    public void setNodeId(Integer nodeId) {
        this.nodeId = nodeId;
    }

    public Integer getAreaId() {
        return areaId;
    }

    public void setAreaId(Integer areaId) {
        this.areaId = areaId;
    }

    public Integer getProductId() {
        return productId;
    }

    public void setProductId(Integer productId) {
        this.productId = productId;
    }

    public String getSubscriber() {
        return subscriber;
    }

    public void setSubscriber(String subscriber) {
        this.subscriber = subscriber;
    }

    public String getRealname() {
        return realname;
    }

    public void setRealname(String realname) {
        this.realname = realname;
    }

    public String getPassword() {
        return password;
    }

    public void setPassword(String password) {
        this.password = password;
    }

    public String getBillType() {
        return billType;
    }

    public void setBillType(String billType) {
        this.billType = billType;
    }

    public String getDomain() {
        return domain;
    }

    public void setDomain(String domain) {
        this.domain = domain;
    }

    public String getAddrPool() {
        return addrPool;
    }

    public void setAddrPool(String addrPool) {
        this.addrPool = addrPool;
    }

    public String getPolicy() {
        return policy;
    }

    public void setPolicy(String policy) {
        this.policy = policy;
    }

    public Integer getActiveNum() {
        return activeNum;
    }

    public void setActiveNum(Integer activeNum) {
        this.activeNum = activeNum;
    }

    public Integer getIsOnline() {
        return isOnline;
    }

    public void setIsOnline(Integer isOnline) {
        this.isOnline = isOnline;
    }

    public BigInteger getFlowAmount() {
        return flowAmount;
    }

    public void setFlowAmount(BigInteger flowAmount) {
        this.flowAmount = flowAmount;
    }

    public Boolean getBindMac() {
        return bindMac;
    }

    public void setBindMac(Boolean bindMac) {
        this.bindMac = bindMac;
    }

    public Boolean getBindVlan() {
        return bindVlan;
    }

    public void setBindVlan(Boolean bindVlan) {
        this.bindVlan = bindVlan;
    }

    public String getIpAddr() {
        return ipAddr;
    }

    public void setIpAddr(String ipAddr) {
        this.ipAddr = ipAddr;
    }

    public String getMacAddr() {
        return macAddr;
    }

    public void setMacAddr(String macAddr) {
        this.macAddr = macAddr;
    }

    public Integer getInVlan() {
        return inVlan;
    }

    public void setInVlan(Integer inVlan) {
        this.inVlan = inVlan;
    }

    public Integer getOutVlan() {
        return outVlan;
    }

    public void setOutVlan(Integer outVlan) {
        this.outVlan = outVlan;
    }

    public BigDecimal getUpRate() {
        return upRate;
    }

    public void setUpRate(BigDecimal upRate) {
        this.upRate = upRate;
    }

    public BigDecimal getDownRate() {
        return downRate;
    }

    public void setDownRate(BigDecimal downRate) {
        this.downRate = downRate;
    }

    public BigDecimal getUpPeakRate() {
        return upPeakRate;
    }

    public void setUpPeakRate(BigDecimal upPeakRate) {
        this.upPeakRate = upPeakRate;
    }

    public BigDecimal getDownPeakRate() {
        return downPeakRate;
    }

    public void setDownPeakRate(BigDecimal downPeakRate) {
        this.downPeakRate = downPeakRate;
    }

    public String getUpRateCode() {
        return upRateCode;
    }

    public void setUpRateCode(String upRateCode) {
        this.upRateCode = upRateCode;
    }

    public String getDownRateCode() {
        return downRateCode;
    }

    public void setDownRateCode(String downRateCode) {
        this.downRateCode = downRateCode;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getBeginTime() {
        return beginTime;
    }

    public void setBeginTime(String beginTime) {
        this.beginTime = beginTime;
    }

    public String getExpireTime() {
        return expireTime;
    }

    public void setExpireTime(String expireTime) {
        this.expireTime = expireTime;
    }

    public String getCreateTime() {
        return createTime;
    }

    public void setCreateTime(String createTime) {
        this.createTime = createTime;
    }

    public String getUpdateTime() {
        return updateTime;
    }

    public void setUpdateTime(String updateTime) {
        this.updateTime = updateTime;
    }

    public String getRemark() {
        return remark;
    }

    public void setRemark(String remark) {
        this.remark = remark;
    }
}
