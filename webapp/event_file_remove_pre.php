<html>
<head>
<meta name="viewport" content="width=device-width, user-scalable=no">
<title>무인관리시스템 음성파일 삭제</title>
</head>
<body> 

<center>
<br>
<?php
$file_id   = $_REQUEST['file_id'];
$name_orig = $_REQUEST['name_orig'];
$name_save = $_REQUEST['name_save'];

?>
<!-- 입력된 값을 다음 페이지로 넘기기 위해 FORM을 만든다. -->
<form action=event_file_remove.php?file_id=<?= $file_id ?>&name_orig=<?= $name_orig ?>&name_save=<?= $name_save ?> method=post>

<table width=300 border=1 cellpadding=2 cellspacing=1>
<tr>
<td height=20 align=center bgcolor=ff3333>
<font color=white><B>비 밀 번 호 확 인</B></font>
</td>
</tr>
<tr>
<td align=center >
<font color=black><B>비밀번호 : </b>
<INPUT type=password name=pass size=20 maxlength=20>
<INPUT type=submit value="확 인">
<INPUT type=button value="취 소" onclick="history.back(-1)">
</td>
</tr>
</table>
</form>
