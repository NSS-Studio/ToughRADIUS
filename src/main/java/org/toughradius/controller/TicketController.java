package org.toughradius.controller;

import org.toughradius.common.PageResult;
import org.toughradius.common.RestResult;
import org.toughradius.common.ValidateUtil;
import org.toughradius.component.TicketCache;
import org.toughradius.entity.RadiusTicket;
import org.toughradius.entity.TraceMessage;
import org.toughradius.component.Syslogger;
import org.toughradius.component.ServiceException;
import org.toughradius.component.RadiusStat;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.Map;

@RestController
public class TicketController {

    @Autowired
    private TicketCache ticketCache;

    @Autowired
    private Syslogger logger;

    @GetMapping("/admin/ticket/query")
    public PageResult<RadiusTicket> queryTicket(@RequestParam(defaultValue = "0") int start,
                                                @RequestParam(defaultValue = "40") int count,
                                                String startDate,
                                                String endDate,
                                                String nasid,
                                                String nasaddr,
                                                Integer nodeId,
                                                Integer areaId,
                                                String username,
                                                String keyword){

        try {
            return ticketCache.queryTicket(start,count,startDate,endDate, nasid, nasaddr, nodeId, areaId, username,keyword);
        } catch (ServiceException e) {
            logger.error(String.format("/admin查询上网日志发生错误, %s", e.getMessage()),e,Syslogger.SYSTEM);
            return new PageResult<RadiusTicket>(start,0, new ArrayList<RadiusTicket>());
        }
    }
}
