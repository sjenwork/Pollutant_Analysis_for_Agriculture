SELECT com.ComFacBizType, com.AdminNo, com.ComFacBizAdminNo, com.ComFacBizFactoryRegNo, com.ComFacBizName, com.ComFacBizAddr, com.RegularAddr, com.OptBehavior,
gis.RegularAddress, gis.CompanyAddress, gis.CompanySegAddress, gis.TWD97TM2X, gis.TWD97TM2Y, gis.[Type], gis.msg
from ComFacBizMappingInfo com
left join GISMappingTWD97 gis
on com.ComFacBizType = gis.ComFacBizType and com.AdminNo = gis.AdminNo


SELECT com.ComFacBizType, com.AdminNo, com.ComFacBizAdminNo, com.ComFacBizFactoryRegNo, com.ComFacBizName, com.ComFacBizAddr, com.RegularAddr, com.OptBehavior,
gis.RegularAddress, gis.CompanyAddress, gis.CompanySegAddress, gis.TWD97TM2X, gis.TWD97TM2Y, gis.[Type], gis.msg
from ComFacBizMappingInfo com
left join GISMappingTWD97 gis
on com.ComFacBizType = gis.ComFacBizType and com.AdminNo = gis.AdminNo