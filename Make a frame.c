#include "includes.h"
void make_frame(char *send_buf,unsigned char cmd,int *send_size)
{
	HEADER header;
	char vlen_payload[100] = {0};
	unsigned char i = 0;
	if(cmd == OPCODE_MUST_LOGIN_FIRST_ERROR)
	{
		memset(&header,0,sizeof(HEADER));
		header.magic1 = 0xff;
		header.magic2 = 0xff;
		header.opcode = cmd;
		header.payload_len = 0;
		for(i = 0;i < 4;i++)
			header.token[i] = 0x11;
		for(i = 0;i < 4;i++)
			header.msg_id[i] = 0x11;
	}
	else if(cmd == OPCODE_SUCCESSFUL_LOGIN_ACK)
	{
		memset(&header,0,sizeof(HEADER));
		header.magic1 = 0xff;
		header.magic2 = 0xff;
		header.opcode = cmd;
		header.payload_len = 0;
		for(i = 0;i < 4;i++)
			header.token[i] = 0x11;
		for(i = 0;i < 4;i++)
			header.msg_id[i] = 0x11;
	}
	//else if()
	send_buf[0] = header.magic1;
	send_buf[1] = header.magic2;
	send_buf[2] = header.opcode;
	send_buf[3] = header.payload_len;
	sprintf(&send_buf[4],"%s",header.token);
	sprintf(&send_buf[8],"%s",header.msg_id);
	if(header.payload_len != 0)
		sprintf(send_buf,"%s",vlen_payload);
	*send_size = 12 + header.payload_len;
}
void check_cmd(char *recv_buf)
{

}
