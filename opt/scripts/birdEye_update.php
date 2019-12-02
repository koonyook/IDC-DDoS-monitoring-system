#!/usr/bin/php
<?php
   $ch1 = curl_init();
        curl_setopt ($ch1, CURLOPT_URL, "http://?.?.?.?:8080/tool/updateFromCNSMON/");
        curl_setopt($ch1, CURLOPT_RETURNTRANSFER, 1);
        $result1 = curl_exec ($ch1);
        echo curl_error($ch1);
   curl_close ($ch1);

   $result1 = trim($result1);
   // echo "Equipments update status : ".$result1."\n";

   if($result1 == "\"OK\""){
      // echo "Equipments update status : ".$result1."\n";
	  
      $ch2 = curl_init();
           curl_setopt ($ch2, CURLOPT_URL, "http://?.?.?.?:8080/tool/updateVLAN/");
           curl_setopt($ch2, CURLOPT_RETURNTRANSFER, 1);
           $result2 = curl_exec ($ch2);
           echo curl_error($ch2);
	  curl_close ($ch2);

      $result2 = trim($result2);
      // echo "VLAN update status : ".$result2."\n";

      if($result2 == "\"OK\""){
           echo "Equipments update status : ".$result1."\n";
		   echo "VLAN update status : ".$result2."\n";
      }
      else{
           echo "Equipments update status : ".$result1."\n";
           echo "Update VLAN uncompleted!!! \n";  
           echo "VLAN error status : ".$result2."\n";
      }
    }
   else {
	  echo "Update Equipments uncompleted!!! \n";  
      echo "Equipments error status : ".$result1."\n";
   }
?>
