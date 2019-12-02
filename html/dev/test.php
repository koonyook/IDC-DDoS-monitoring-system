#keyType can be 'password' or 'hash'

<?php
	
	function is_valid_string($var)
	{
		if (is_string($var) && $var!="")	
			return TRUE;
		else
			return FALSE;
	}

	function NThash($plainText)
	{
		if (is_valid_string($plainText))
		{
			list($LM,$NT) = split("\t",exec("smbencrypt ".$plainText));
			return $NT;
		}
		else
		{
			return NULL;
		}
	}
	
	#echo NThash("difficult");
	
	function is_valid_key($key,$keyType)
	{
		if (!is_valid_string($keyType) || !is_valid_string($key))
			return FALSE;
		if ($keyType!="password" && $keyType!="hash")
			return FALSE;
		
		return TRUE;
	}
	
	function get_hash_from_key($key,$keyType)
	{
		if ($keyType=="password")
			return NThash($key);
		elseif ($keyType=="hash")
			return $key;
		else
			return NULL;
	}

	#global settings
	$DBAddress="?.?.?.?";
	$DBName="radius";
	$DBUsername="?";
	$DBPassword="?";
	$groupName="test_group";
	
	function connect_db()
	{
		$con=mysqli_connect($GLOBALS["DBAddress"],$GLOBALS["DBUsername"],$GLOBALS["DBPassword"],$GLOBALS["DBName"]);
		#Check connection
		if (mysqli_connect_errno($con))
		{
			#echo "Failed to connect to MySQL: " . mysqli_connect_error();
			return NULL;
		}
		#echo "Connection OK";
		return $con;																																		
	}

	function isUserAppear($username)
	{
		if (!is_valid_string($username))
			return NULL;

		$con=connect_db();
		if ($con==NULL)
			return NULL;
		else
		{
			$result1=mysqli_query($con, "SELECT * FROM radcheck WHERE username='".$username."';");
			$result2=mysqli_query($con, "SELECT * FROM radusergroup WHERE username='".$username."';");
			
			if ($result1->num_rows==$result2->num_rows)
				$answer=$result1->num_rows;
			else
				return NULL;
		}
		mysqli_close($con);
		
		if ($answer==0)
			return FALSE;
		elseif ($answer==1)
			return TRUE;
		else
			return NULL;
	}

	#echo isUserAppear('test');
	
	function addUser($username,$key,$keyType)
	{
		if (is_valid_string($username) && is_valid_key($key,$keyType) && !isUserAppear($username))
		{
			$hash=get_hash_from_key($key,$keyType);
			$con=connect_db();
			if ($con==NULL)
				return NULL;
			else
			{
				$result1=mysqli_query($con, "INSERT INTO radcheck (id,username,attribute,op,value) VALUES (NULL,'".$username."','NT-Password',':=','".$hash."')");
				$result2=mysqli_query($con, "INSERT INTO radusergroup (username,groupname,priority) VALUES ('".$username."','".$GLOBALS['groupName']."',1)");

				if($result1==TRUE && $result2==TRUE)
					return TRUE;
				else
					return NULL;
			}
		}
		else
			return NULL;
	}
	
	#echo addUser('testee','4321','password');

	function deleteUser($username)
	{
		if (is_valid_string($username) && isUserAppear($username))
		{
			$con=connect_db();
			if ($con==NULL)
				return NULL;
			else
			{
				$result1=mysqli_query($con, "DELETE FROM radcheck WHERE username = '".$username."'");
				$result2=mysqli_query($con, "DELETE FROM radusergroup WHERE username = '".$username."'");
			
				if($result1==TRUE && $result2==TRUE)
					return TRUE;
				else
					return NULL;
			}
		}
		else
			return NULL;
	}
	
	#echo deleteUser('tester');

	function updateUser($username,$key,$keyType)
	{
		if (is_valid_string($username) && is_valid_key($key,$keyType) && isUserAppear($username))
		{
			$hash=get_hash_from_key($key,$keyType);
			$con=connect_db();
			if ($con==NULL)
				return NULL;
			else
			{
				$result=mysqli_query($con, "UPDATE radcheck SET value='".$hash."' WHERE username='".$username."'");

				if($result==TRUE)
					return TRUE;
				else
					return NULL;
			}
		}
		else
			return NULL;
	}
	
	#echo updateUser('tester','1234','password');
?>
