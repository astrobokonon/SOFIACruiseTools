<?xml version="1.0" encoding="UTF-8" ?>
<!-- XSL stylesheet to render SOFIADictionary into Descriptions.-->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:template match="/">
<html>
<HEAD>
 <TITLE>SOFIA Keywords | Descriptions</TITLE>
	<META NAME="author" CONTENT="R. Y. Shuping"></META>
</HEAD>
  <body>

    <h2> Keyword Descriptions </h2>

   <xsl:for-each select="KeywordDictionary/KeywordList">
       <h3> <xsl:value-of select="@title"/> </h3>
            <xsl:for-each select="Keyword/Requirement">
	    <dl><FONT SIZE="-1">
            <dt><B><U><xsl:value-of select="../@title"/></U></B></dt>
            <dt> <B>FITS Name:</B>    <xsl:value-of select="../FITS/@name"/> </dt>
            <dt> <B>FITS Type:</B>    <xsl:value-of select="../FITS/@type"/> </dt>
             <dt> <B>Description:</B>  <xsl:value-of select="../Description"/> </dt>
             <dt> <B>Requirement:</B>   <xsl:value-of select="../Requirement/@condition"/> </dt></FONT>
             </dl>
             </xsl:for-each>
   </xsl:for-each>
</body>
</html>
</xsl:template>
</xsl:stylesheet>