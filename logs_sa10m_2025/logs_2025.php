<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html"; charset=utf-8"/> 
<meta name="viewport" content="width=device-width, initial-scale=1">

<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous">

<style>
* {
  box-sizing: border-box;
}

input[type=text], select, textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: vertical;
}

label {
  padding: 12px 12px 12px 0;
  display: inline-block;
}

input[type=submit] {
  background-color: #57a5cf;
  color: white;
  padding: 12px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  float: right;
}

input[type=submit]:hover {
  background-color: #4d85a3;
}

.container {
  border-radius: 5px;
  background-color: #f2f2f2;
  padding: 20px;
}

.col-25 {
  float: left;
  width: 25%;
  margin-top: 6px;
}

.col-75 {
  float: left;
  width: 75%;
  margin-top: 6px;
}

/* Clear floats after the columns */
.row:after {
  content: "";
  display: table;
  clear: both;
}

/* Responsive layout - when the screen is less than 600px wide, make the two columns stack on top of each other instead of next to each other */
@media screen and (max-width: 600px) {
  .col-25, .col-75, input[type=submit] {
    width: 100%;
    margin-top: 0;
  }
}
/* Rounded border */
hr.rounded {
  border-top: 8px solid #bbb;
  border-radius: 5px;
}
table {
  border-collapse: collapse;
  border-spacing: 0;
  width: 100%;
  border: 1px solid #ddd;
}

th, td {
  text-align: left;
  padding: 8px;
}

tr:nth-child(even){background-color: #f2f2f2}
</style>


<style>
.alert {
  padding: 20px;
  background-color: #f44336;
  color: white;
}

.closebtn {
  margin-left: 15px;
  color: white;
  font-weight: bold;
  float: right;
  font-size: 22px;
  line-height: 20px;
  cursor: pointer;
  transition: 0.3s;
}

.closebtn:hover {
  color: black;
}
</style>
<style>
.alert2 {
  padding: 20px;
  background-color: #317d48;
  color: white;
}

.closebtn {
  margin-left: 15px;
  color: white;
  font-weight: bold;
  float: right;
  font-size: 22px;
  line-height: 20px;
  cursor: pointer;
  transition: 0.3s;
}

.closebtn:hover {
  color: black;
}
</style>
</head>
<body>

<?php

if (!ini_get('display_errors')) {
    ini_set('display_errors', '1');
}


$dir    ='/home/u283109477/domains/sa10m.com.ar/public_html/2025/logs';

$files2 = scandir($dir, SCANDIR_SORT_ASCENDING);


for ($x = 0; $x <= count($files2); $x++) {
    if($files2[$x]<>'logs_2025.php' AND $files2[$x]<>'.' AND $files2[$x]<>'..'){
    //echo $files2[$x]."<br>";
    //echo "https://sa10m.com.ar/2025/logs/".$files2[$x]."<br>";
    echo '<a href="https://sa10m.com.ar/2025/logs/'.$files2[$x].'">'.$files2[$x].'</a><br>';
  }
}

//print_r($files2);
































exit;

			$Salida=json_encode($SaleArray);
			Guarda_Archivo($path.'resultados/jsons/wwargdx_2025.json', $Salida);

/////////////////////////////////////////// fin //////////////////////////////////////////

function hacerFizcalizado($sucio, $estacion, $opes, $categoria, $subcategoria, $capaModo, $capaBanda, $nombre, $overlay, $puntosFinal, $email){
Global $dbhost;
Global $dbname;
Global $dbuser;
Global $dbpass;	Global $sucio;
echo 'Su: '.$sucio.'<br>'; exit;
$puntos_FinalPH=0; $puntos_FinalCW=0; 
$MM_FinalCW=0; $MM_FinalPH=0;$texto='';$estacion_sinBarra=str_replace("/","_",$estacion);
echo '<a href="https://worldwideargentina.com.ar/php/fiscalizados/'.$estacion_sinBarra.'_'.$sucio.'.txt" target="_blank">'.$estacion.'_'.$sucio.'</a><br>';
$texto='*********************************************************************************'.PHP_EOL;
$texto=$texto.'2025 WW Argentina DX Contest'.PHP_EOL;
$texto=$texto.'*********************************************************************************'.PHP_EOL;
$texto=$texto.'         CallSign: '.$estacion.PHP_EOL;
$texto=$texto.'             Name: '.$nombre.PHP_EOL;
$texto=$texto.'        Operators: '.$opes.PHP_EOL;
$texto=$texto.'CATEGORY-OPERATOR: '.$categoria.PHP_EOL;
$texto=$texto.'   CATEGORY-POWER: '.$subcategoria.PHP_EOL;
$texto=$texto.'    CATEGORY-MODE: '.$capaModo.PHP_EOL;
$texto=$texto.'    CATEGORY-BAND: '.$capaBanda.PHP_EOL;
$texto=$texto.' CATEGORY-OVERLAY: '.$overlay.PHP_EOL;
$texto=$texto.'            EMAIL: '.$email.PHP_EOL;
$texto=$texto.'---------------------------------------------------------------------------------'.PHP_EOL;
$conexion = mysqli_connect($dbhost, $dbuser, $dbpass, $dbname);			
$sql = "SELECT * FROM control_new WHERE yo='$estacion' order by fecha asc";
$result = mysqli_query($conexion, $sql);
while($obtener_filas=mysqli_fetch_array($result)){
$banda=$obtener_filas['banda'];
$modo=$obtener_filas['modo'];
$fecha=$obtener_filas['fecha'];
$date = substr($fecha, 0, 16); 
$yo=$obtener_filas['yo'];
///////////////////////////////////////////////
$largo=strlen($yo); $espacios='';
for($i=$largo; $i<10; $i++){
	$espacios=$espacios.' ';
}
$yo_x=$yo.$espacios;
//////////////////////////////////////////////////////
$miserie=$obtener_filas['miserie'];
$el=$obtener_filas['el'];
///////////////////////////////////////////////
$largo=strlen($el);$espacios='';
for($i=$largo; $i<10; $i++){
	$espacios=$espacios.' ';
}
$el_x=$el.$espacios;
//////////////////////////////////////////////////////
$suserie=$obtener_filas['suserie'];
$aclaracion=$obtener_filas['aclaracion'];

if ($aclaracion=='OK'){
	$puntos=$obtener_filas['puntos'];
	$multiPFX=$obtener_filas['multiPFX'];
	
	$pm='';
if($multiPFX<>''){
		$pm=' M: '.$multiPFX;
	if($modo=='CW'){
	$MM_FinalCW=$MM_FinalCW+1;
    } else {
	$MM_FinalPH=$MM_FinalPH+1;	
	}		
}
$puntos_d=number_format($puntos,0);
$puntos_d=str_replace(",",".",$puntos_d).' km.';
	$aclaracion='P: '.$puntos_d.$pm;

if($modo=='CW'){
	$puntos_FinalCW=$puntos_FinalCW+$puntos;

    } else {
	$puntos_FinalPH=$puntos_FinalPH+$puntos;	
}
}
$texto=$texto.$banda.' '.$modo.' '.$date.' '.$yo_x.' '.$miserie.' '.$el_x.' '.$suserie.'    '.$aclaracion.PHP_EOL;
}
$texto=$texto.'---------------------------------------------------------------------------------'.PHP_EOL;

$puntos_FinalCW_d=number_format($puntos_FinalCW,0);
$puntos_FinalCW_d=str_replace(",",".",$puntos_FinalCW_d);
$texto=$texto.'CW Points: '.$puntos_FinalCW_d.PHP_EOL;

$MM_FinalCW_d=number_format($MM_FinalCW,0);
$MM_FinalCW_d=str_replace(",",".",$MM_FinalCW_d);
$texto=$texto.'CW  Grids: '.$MM_FinalCW_d.PHP_EOL;

$CWScore_d=$puntos_FinalCW*$MM_FinalCW;
$CWScore_d=number_format($CWScore_d,0);
$texto=$texto.'CW  Score: '.$CWScore_d.PHP_EOL;
$texto=$texto.'---------------------------------------------------------------------------------'.PHP_EOL;
$puntos_FinalPH_d=number_format($puntos_FinalPH,0);
$puntos_FinalPH_d=str_replace(",",".",$puntos_FinalPH_d);
$texto=$texto.'SSB Points: '.$puntos_FinalPH_d.PHP_EOL;

$MM_FinalPH_d=number_format($MM_FinalPH,0);
$MM_FinalPH_d=str_replace(",",".",$MM_FinalPH_d);
$texto=$texto.'SSB  Grids: '.$MM_FinalPH_d.PHP_EOL;

$SSBScore=$puntos_FinalPH*$MM_FinalPH;
$SSBScore_d=number_format($SSBScore,0);
$SSBScore_d=str_replace(",",".",$SSBScore_d);
$texto=$texto.'SSB  Score: '.$SSBScore_d.PHP_EOL;


$grand=$puntos_FinalCW*$MM_FinalCW+$puntos_FinalPH*$MM_FinalPH;
$grand_d=number_format($grand,0);
$grand_d=str_replace(",",".",$grand_d);
$texto=$texto.'---------------------------------------------------------------------------------'.PHP_EOL;
$texto=$texto.'Final Score: '.$grand_d.PHP_EOL;
$texto=$texto.'---------------------------------------------------------------------------------'.PHP_EOL.PHP_EOL.PHP_EOL;
$texto=$texto.'References:'.PHP_EOL;
$texto=$texto.'*Exchange: xxxx  >Failure in received exchange.'.PHP_EOL;
$texto=$texto.'*BadCall:        >Wrong station.'.PHP_EOL;
$texto=$texto.'*DUPE:           >Previously worked station.'.PHP_EOL;
$texto=$texto.'*NIL:            >Not in Log, the station has not been registered your Callsign.'.PHP_EOL;
$texto=$texto.'*Time Error:     >QSO not in Contest Date/Time.'.PHP_EOL;
$texto=$texto.'*CHECKLOG:       >Not band/mode QSO reported.'.PHP_EOL;
$texto=$texto.'---------------------------------------------------------------------------------'.PHP_EOL;
$sucio=$sucio+1;
Guarda_Archivo(trim($yo).'_'.$sucio.'.txt', $texto);
$texto_mail=$estacion.';https://worldwideargentina.com.ar/php/fiscalizados/'.$estacion.'_'.$sucio.'.txt;'.$email.PHP_EOL;

Guarda_Archivo_mails('mails.csv', $texto_mail);
}

function Guarda_Archivo($nombre, $texto){
$nombre=str_replace("/","_",$nombre);
$path='/home/u343989035/domains/worldwideargentina.com.ar/public_html/php/fiscalizados/'.$nombre;
$myfile = fopen($path, "w") or die("Unable to open file!");
fwrite($myfile,$texto);
fclose($myfile); 
}
function Guarda_Archivo_mails($nombre, $texto){
$path='/home/u343989035/domains/worldwideargentina.com.ar/public_html/php/fiscalizados/'.$nombre;
//echo $texto.'<br>';
$myfile = fopen($path, "a") or die("Unable to open file!");
fwrite($myfile,$texto);
fclose($myfile); 
}
function BorrarSiHay($filename){ 
$filename='/home/u343989035/domains/worldwideargentina.com.ar/public_html/php/fiscalizados/'.$filename;
if (file_exists($filename)) {
	unlink($filename);
}
}
function LevantaMails($Quien){
$dbhost='localhost';
$dbname='u343989035_Pata_2025';
$dbuser='u343989035_Pata_2025';
$dbpass='Rojocampeon_2013';	
	$suEmail='';
$conexion = mysqli_connect($dbhost, $dbuser, $dbpass, $dbname);			
$sql = "SELECT * FROM Recibidos_2025_ver where estacion='$Quien'";
$result = mysqli_query($conexion, $sql);
while($obtener_filas=mysqli_fetch_array($result)){
$suEmail=$obtener_filas['mail'];	
}
return $suEmail;	
}
?>

