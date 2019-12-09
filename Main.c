#include "includes.h"
#define CLIENT_NUM_MAX 100 

struct sockaddr_in current_client_addr;
struct sockaddr_in server;

FILE_CONTEXT file_context[CLIENT_NUM_MAX];
int online_client_num = 0;
unsigned char index_client = 0;
char tmp_recv_payload[100] = {0};
char dst[2][100] = {0};
char tmp_name[10] = {0};
char tmp_secret[7] = {0};
char recv_buf[1024] = {0};
char send_buf[1000] = {0};

NETINFO netinfo[100];

void strsplit(char *src,char flag,char dst[2][100])
{
	unsigned char i = 0;
	char *tmp = &dst[i][0];
	while(*src != '\0')
	{
		if(*src == flag)
		{
			*tmp = '\0';
			tmp = &dst[++i][0];
			src++;
		}
		*tmp++ = *src;
		src++;
	}
}
void get_time(char *time)
{
	struct timeval tv;
	struct timezone tz;
	gettimeofday(&tv,&tz);
	//sprintf(time,"%s.%s.%s",);
	//printf(¡°tv_sec:%d\n¡±,tv.tv_sec);
	//printf(¡°tv_usec:%d\n¡±,tv.tv_usec);
	//printf(¡°tz_minuteswest:%d\n¡±,tz.tz_minuteswest);
	//printf(¡°tz_dsttime:%d\n¡±,tz.tz_dsttime);
}

void *handle_client(void *tmp_netinfo)
{
	//int conm_socket = *(int*)v;
	NETINFO *netinfo = tmp_netinfo;
	STATE state = LOGIN; //µ±Ç°×´Ì¬ÊÇµÇÂ¼Ì¬
	char send_buf[1024] = {0};
	int send_size = 0;
	make_frame(send_buf,OPCODE_SUCCESSFUL_LOGIN_ACK,&send_size);
	sendto(netinfo->sockfd, send_buf, send_size, 0, (struct sockaddr *)&netinfo->client,  sizeof(struct sockaddr_in));
	switch(state)
	{
		case LOGIN:break;
		case NO_LOGIN:break;
		case MSG_FORWARD:break;
	}
}
bool readfile(char* strFile)
{
    FILE *fp;
    char cLineBuffer[100] = {0};
    char str0[] = "*";
	char *result = NULL;
	char dst[2][100] = {0};
    fp=fopen(strFile,"r");

    if(fp == NULL)
    {
        printf("can not open the config file %s",strFile);
        return false;
    }
    while(fgets(cLineBuffer,100,fp)!=(char *) NULL)
    {
		//printf("cLineBuffer is %s",cLineBuffer);
		memset(dst,0,200);
		strsplit(cLineBuffer,'*',dst);
		//printf("dst[0] is %s,dst[1] is %s",dst[0],dst[1]);
		memset(&file_context[index_client],0,sizeof(FILE_CONTEXT));
		strcpy(file_context[index_client].name,dst[0]);
		// printf("%s ", result);
		//strcpy(tmp, result);
		//printf("%s^",tmp);
		strcpy(file_context[index_client].secret,dst[1]);
		index_client ++;
    }
    fclose(fp);
    return true;
}
void send_data(int conm_socket, char *send_buf,int send_size)
{

	// ½ÓÊÕ·½µÄµØÖ·
	//struct sockaddr_in addr;
	//memset(&addr, 0, sizeof(struct sockaddr_in));
	//addr.sin_family      = AF_INET;                      /* InternetµØÖ·×å */
	//addr.sin_port        = htons(atoi(argv[2]));         /*·þÎñÆ÷ÓÃµÄ¶Ë¿ÚºÅ */
	//addr.sin_addr.s_addr = inet_addr(argv[1]);           /*·þÎñÆ÷ÓÃµÄIPµØÖ· */

	//char buf[1024];
	//while (1)
	//{
	//	printf("input data:\n");
	//	scanf("%s",buf);
		//fgets(buf, 1024, stdin);
		sendto(conm_socket, send_buf, send_size, 0, (struct sockaddr *)&current_client_addr,  sizeof(struct sockaddr_in));
	//}

}

void recv_data(int conn_socket)
{
	char time[20] = {0};
	int  send_size = 0;
	unsigned char i = 0;
	pthread_t thread;
	int ret = 0;
	socklen_t len = sizeof(struct sockaddr_in);
	printf("recv_data");
	while (1)
	{
		memset(&current_client_addr, 0, sizeof(struct sockaddr_in));
		memset(recv_buf,0,1024);
		memset(dst,0,200);
		ret = recvfrom(conn_socket, recv_buf, 1023, 0, (struct sockaddr *)&current_client_addr, &len);//×èÈûÊ½½ÓÊÕ
		printf("ret is %d",ret);
		if (-1 == ret)
		{
			perror ("read error");
		}
		if (0 == ret)
		{
			printf ("¿Í»§¶ËÍË³ö\n");
			break;
		}
		else if(ret == (12+recv_buf[3]))
		{
			//memset(tmp_recv_payload,0,100);
			if(OPCODE_LOGIN == recv_buf[2])//ÊÇ¾Í´´½¨Ïß³Ì£¬1¶Ô1»á»°
			{
				if(recv_buf[3] == 0)//·¢ËÍµÄÊý¾ÝÓÐÎÊÌâ
				{
					make_frame(send_buf,OPCODE_MUST_LOGIN_FIRST_ERROR,&send_size);
					send_data(conn_socket, send_buf,send_size);
					continue;
				}
				while(i < recv_buf[3])
				{
					tmp_recv_payload[i] = recv_buf[12+i];
					i++;
				}
				tmp_recv_payload[i] = 0;
				strsplit(tmp_recv_payload,'*',dst);
				strcpy(tmp_name,dst[0]);
				strcpy(tmp_secret,dst[1]);
				for(i = 0;i < index_client;i++)
				{
					if((strcmp(tmp_name,file_context[i].name) == 0) && \
						(strcmp(tmp_secret,file_context[i].secret) == 0))
					{
						file_context[i].on_line_flag = 1;
						memset(&netinfo[online_client_num],0,sizeof(NETINFO));
						netinfo[online_client_num].sockfd = conn_socket;
						netinfo[online_client_num].client= current_client_addr;
						pthread_create(&thread, NULL, handle_client, &netinfo[online_client_num]);
						if(online_client_num < 100)//ÔÊÐíÍ¬Ê±ÔÚÏßµÄ¿Í»§¶ËÊýÄ¿Îª100
							online_client_num ++;
						break;
					}
				}
			}
			else//Èç¹û²»ÊÇµÇÂ¼£¬¾Í»ØOPCODE_MUST_LOGIN_FIRST_ERROR
			{
				make_frame(send_buf,OPCODE_MUST_LOGIN_FIRST_ERROR,&send_size);
				send_data(conn_socket, send_buf,send_size);
			}
		}
		//get_time(time);
		/*´òÓ¡¿Í»§¶ËµØÖ·ºÍ¶Ë¿ÚºÅ*/
        //inet_ntop(AF_INET,&current_client_addr.sin_addr,addr_p,sizeof(addr_p));
        //printf("client IP is %s, port is %d\n",addr_p,ntohs(client.sin_port));
		//sprintf(str_port,"%d",ntohs(current_client_addr.sin_port));
		//sprintf(disp,"[ %s ip:%s ,port:%d]:%s",time,addr_p,str_port,recv_buf);
		//recv_buf[ret] = '\0';
		//printf ("%s\n", disp);
	}
}

int GetIP(char *IP)
{						/* Retrieve the client's IP address */
	//char hostname[128];
	//struct addrinfo hints, *res;
	//struct in_addr addr;
	//int err;

	//gethostname(hostname, sizeof(hostname));

	/* Variables to be used by the getaddrinfo function */
	//memset(&hints, 0, sizeof(hints));
	//hints.ai_socktype = SOCK_STREAM;
	//hints.ai_family = AF_INET;

	//if (getaddrinfo(hostname, NULL, &hints, &res) != 0)
	//{
	//	return 1;
	//}

	/* Parse the addr variable for the IP address */
	//addr.s_addr = ((struct sockaddr_in *)(res->ai_addr))->sin_addr.s_addr;

	/* Copy the IP to the string passed into this function */
	//strcpy(IP, inet_ntoa(addr));

	/* Free res */
	//freeaddrinfo(res);

	/* Print the IP address */
	//printf("IP: %s\n", IP);

	//return 0;
}
int main(int argc, char **argv)
{

	if ((argc < 3) || (argc > 4))		/* Test for correct number of arguments */
	{
		fprintf(stderr,"Usage: %s <Server IP> <Port Number>\n", argv[0]);
		exit(1);
	}
	// 1¡¢´´½¨Ì×½Ó×Ö
	int conn_socket = socket(AF_INET, SOCK_DGRAM, 0);
	if(-1 == conn_socket)
	{
		perror("´´½¨Ì×½Ó×ÖÊ§°Ü");
		return -1;
	}
	bzero(&server, sizeof(server));
    server.sin_family = AF_INET;
	//server.sin_addr.s_addr = htonl(INADDR_ANY);//inet_addr(argv[1]);
	server.sin_port = htons(atoi(argv[2]));
	if(-1 == ( bind( conn_socket, ( struct sockaddr * )&server, sizeof(server) )) )
    {
        perror("bind error");
        exit (1);
    }
	if(false == readfile("./inc.txt"))
	{
		printf("server start failed!!!");
		close(conn_socket);
		return 0;
	}
	recv_data(conn_socket);
	//pthread_create(&thread, NULL, recv_data, &conn_socket);
	//send_data(conn_socket, argv);
	close(conn_socket);

	return 0;
}
