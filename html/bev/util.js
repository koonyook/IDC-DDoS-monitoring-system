function getReadableSize(sizeInBytes) {

	var i = -1;
	var byteUnits = [' k', ' M', ' G', ' T', 'P', 'E', 'Z', 'Y'];
	do {
		sizeInBytes = sizeInBytes / 1024;
		i++;
	} while (sizeInBytes > 1024);

	return Math.max(sizeInBytes, 0.1).toFixed(1) + byteUnits[i];
};

function pad2(number) {
	return (number < 10 ? '0' : '') + number
}