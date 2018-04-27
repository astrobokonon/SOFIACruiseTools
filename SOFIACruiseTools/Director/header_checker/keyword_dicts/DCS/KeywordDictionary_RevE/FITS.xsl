<?xml version="1.0" encoding="UTF-8" ?>
<!-- XSL stylesheet to render SOFIADictionary into table format.-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
<html>
<HEAD>
 	<TITLE>SOFIA Keywords | FITS Keywords Rendering</TITLE>
	<META NAME="author" CONTENT="R. Y. Shuping"></META>
</HEAD>

<body>
  <h2> SOFIA Keywords Dictionary </h2>
       <p> [ <B>Version:</B> <xsl:value-of select="KeywordDictionary/@version"/>]
           [<B>Date</B>: <xsl:value-of select="KeywordDictionary/@date"/>  ]</p>

  <h3> FITS Keywords Table </h3>
  <p>All FITS files submitted to the DCS for archiving must adhere to the FITS standard (v3.0, 2008 July 10)</p>
  <p>WCS Keywords (see Array Detector Keywords section) should adhere to standard conventions (see http://fits.gsfc.nasa.gov/fits_wcs.html and http://tdc-www.harvard.edu/wcstools/wcstools.fits.html for discussion and references). </p>
	<DL><FONT size="-2">
  	<DT><B>FITS Name</B>: Keyword name - generally not the same as the abstract title.</DT>
  	<DT><B>Comment</B>: Short description of keyword - suitable for FITS comment fields.  Long descriptions can be found in the detailed descriptions.  Comment text should include units as well. </DT>
	<DT><B>HDU</B>:  header data unit - where the keyword can be used in the FITS file. </DT>
	<DT><B>Representation</B> : How the value of the keyword should be represented.  In simple cases this may just be "string" or "float", but more complicated formats can be specified here (e.g. date and time)</DT>
	<DT><B>Type</B>:  Specific FITS type - integer, float, string, or logical (boolean). </DT>
	<DT><B>Units</B>: Required units for keyword, if applicable.</DT>
	<DT><B>Range</B>: Possible keyword values, including enumerated types.</DT>
	<DT><B>Example</B>: Value example.</DT>
	<DT> <B>Requirement</B> :  Condition for which the keyword is required -- if blank, then the keyword is always required.  Keywords marked with an asterisk ('*') are required for archive ingestion:  If any of these is missing, the host file must be corrected and then re-ingested. </DT>
	<DT><B>Source</B>:  Provider and location, if blank then data provided by SI.  Known pre-defined aliases for some of the MCCS HK data items are included.  We recommend the SI developers assign custom aliases to the others as well for ease of reference.</DT>
	<DT><B>Missing Data Sources</B>: If the HK datanode is not available, or returns NotFound (or any other error), then the following values should be used to populate the corresponding FITS keyword based on the FITS keyword datatype (float, int, str, bool):  FLOAT = -9999.0; INT = -9999; STRING = UNKNOWN; BOOL = defined on keyword by keyword basis.  For missing RA and Dec values, use the string representation with "UNKNOWN".  </DT>
	</FONT>
	</DL>


  <xsl:for-each select="KeywordDictionary/KeywordList">
         <h3> <xsl:value-of select="@title"/> </h3>
         <table border="1">
 		<tr VALIGN="top">
 			<th><div align="left"><FONT size="-2" COLOR="#0000FF">Parameter</FONT></div></th>
    		<th><div align="left"><FONT size="-2" COLOR="#0000FF">FITS Keyword</FONT></div></th>
    		<th width="175"><div align="left"><font size="-2" color="#0000FF">Comment</font></div></th>
    		<th><font size="-2" color="#0000FF">HDU</font></th>
    		<th><font size="-2" color="#0000FF">Representation</font></th>
    		<th><font size="-2" color="#0000FF">Type</font></th>
    		<th><font size="-2" color="#0000FF">Units</font></th>
    		<th><font size="-2" color="#0000FF">Range</font></th>
    		<th><font size="-2" color="#0000FF">Example</font></th>
    		<th><div align="left"><font size="-2" color="#0000FF">Requirement</font></div></th>
  			<th><div align="left"><font size="-2" color="#0000FF">Source</font></div></th>
		</tr>

<!--	  <xsl:for-each select="Keyword/Requirement[@phase='ES']">  -->
	  <xsl:for-each select="Keyword/Requirement">
                 <tr VALIGN="top">
                 <td><div align="left"> <font size="-2"><xsl:value-of select="../@title"/></font></div> </td>
                 <td><div align="left"> <font size="-2"><xsl:value-of select="../FITS/@name"/></font></div> </td>
                 <td><div align="left"> <font size="-2"> <xsl:value-of select="../Comment"/></font></div> </td>
                 <td><div align="center"> <font size="-2"> <xsl:value-of select="../FITS/@hdu"/> </font></div> </td>
                 <td><div align="center"> <font size="-2"> <xsl:for-each select="../Value">[<xsl:value-of select="@representation"/>] </xsl:for-each></font></div> </td>
                 <td><div align="center"> <font size="-2"> <xsl:for-each select="../FITS">[<xsl:value-of select="@type"/>] </xsl:for-each></font></div> </td>
                 <td><div align="center"> <font size="-2"> <xsl:value-of select="../Value/Units"/> </font> </div></td>
                 <td><div align="center"> <font size="-2"> <xsl:value-of select="../Value/Range/@type"/>
		      [<xsl:value-of select="../Value/Range"/>] </font> </div></td>
                 <td><div align="center"> <font size="-2"> <xsl:for-each select="../Value">[<xsl:value-of select="Example"/>] </xsl:for-each> </font> </div></td>
		         <td> <div align="left"><font size="-2"><xsl:value-of select="../Requirement/@condition"/></font></div></td>
		         <td> <div align="left"> <font size="-2"><xsl:value-of select="../Source/@provider"/> : <xsl:value-of select="../Source/@location"/>  </font> </div></td>
                </tr>
          </xsl:for-each>
            	</table>

      </xsl:for-each>
       
</body>
</html>
</xsl:template>
</xsl:stylesheet>