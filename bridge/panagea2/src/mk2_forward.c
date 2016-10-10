/*
 * Copyright (C) 2011 ETSI
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *
 *  Author: ETSI/STF424/Alexandre Berge <alexandre.berge@amb-consulting.com> 
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/time.h>
#include <net/if.h>
#include <net/ethernet.h>
#include <netpacket/packet.h>
#include <arpa/inet.h>

#include "common.h"
#include "mk2mac-api-types.h"

#define BUFSIZE      8192
#define MAX_SRC      32
#define FCS_LENGTH   4
// #define DEVICE_WAVE  "wave-raw"
// Modify for panagea2 
#define DEVICE_WAVE  "wlan0"
#define DEVICE_ETH   "eth0"
#define ID_WAVE      0
#define ID_ETH       1

//#define PANAGEA2_SUPPORT



void * socketRun(void *arg);
int initSocket(char * ifaceName, int etherType);
void forwardPacket(unsigned char * mk2Buf, unsigned char * packetBuf, ssize_t size, int thisSideId, int otherSideId);
void receivePacket(unsigned char * mk2Buf, unsigned char ** packetBuf, ssize_t * size, int thisSideId);
int isMacAddrFromOtherSide(unsigned char * mac, int otherSideId);
int isMacAddressNew(unsigned char * mac, int thisSideId);int mk2_forward(int etherType, uint8_t channel, uint8_t qosAck, uint8_t mcs);
void prepareMk2TxDescriptor(tMK2TxDescriptor * tx, uint8_t channel, uint8_t qosAck, uint8_t mcs);
void dumpBuffer(unsigned char * buffer, int size);

char *devs[2];
int sockets[2];
unsigned char * srcs[2][MAX_SRC];
int srcs_nb[2] = {0, 0};
tMK2TxDescriptor mk2TxDescriptor;

/*
 * @desc   Main function for starting Mk2 forwarding 
 * @param  etherType  EtherType filter
 * @param  channel    Channel number to use for radio transmission
 * @param  qosAck     Acknoledgement mode
 * @param  mcs        Modulation and Coding scheme
 * @return This function returns 0 on success
 */
int mk2_forward(int etherType, uint8_t channel, uint8_t qosAck, uint8_t mcs) {

  int i;
  int err;
  pthread_t thread[2];
  
  devs[ID_WAVE] = DEVICE_WAVE;
  devs[ID_ETH] = DEVICE_ETH;
  prepareMk2TxDescriptor(&mk2TxDescriptor, channel, qosAck, mcs);

  for(i=0; i < 2; i++) {
    sockets[i] = initSocket(devs[i], etherType);
  }

  for(i=0; i < 2; i++) {
    err = pthread_create(&thread[i], NULL, socketRun, (void *)i);
  }

  for(i=0; i < 2; i++) {
    pthread_join(thread[i], NULL);
  }

  return 0;
}

/*
 * @desc   Main loop for receiving and forwarding packets from one interface to the other one
 * @param  arg  ID of the interface associated to this thread (cast to int)
 * @return This function is unlikely to return
 */
void * socketRun(void *arg) {

  int myId = (int)arg;
  int itsId = (myId)?0:1;
  fd_set rfds;
  unsigned char *mk2Buf;
  unsigned char *packetBuf;
  struct ethHdr *eth;
  ssize_t size;

#if DEBUG > 0
  printf("[%s] Starting thread\n", devs[myId]);
#endif

  mk2Buf = (unsigned char *)malloc(BUFSIZE + sizeof(tMK2RxDescriptor) + sizeof(tMK2TxDescriptor));
  packetBuf = mk2Buf;

  FD_ZERO(&rfds);
  FD_SET(sockets[myId], &rfds);
  while(select(sockets[myId] + 1, &rfds, NULL, NULL, NULL) > -1) {

    /* Receive Packet*/
    //size = sizeof(mk2Buf);
    size = BUFSIZE + sizeof(tMK2RxDescriptor) + sizeof(tMK2TxDescriptor);
    receivePacket(mk2Buf, &packetBuf, &size, myId);

    /* Mac Address checks */
    eth = (struct ethHdr *)packetBuf;      
    if(isMacAddrFromOtherSide(eth->src, itsId)) {
      continue; /* loopback => ignore packet */
    }    
    if(isMacAddressNew(eth->src, myId)) {
      srcs[myId][srcs_nb[myId]] = (unsigned char *)malloc(ETHER_ADDR_LEN);
      memcpy(srcs[myId][srcs_nb[myId]++], (char *)(eth->src), ETHER_ADDR_LEN);
    }

    /* Forward Packet */
    forwardPacket(mk2Buf, packetBuf, size, myId, itsId);
    
    /* Flush output buffer */
    fflush(stdout);
  }
  perror("Select failed");
  exit(1);

  return NULL;
}

/*
 * @desc   Forwards packet to interface identified by otherSideId
 * @param  mk2Buf       Pointer to Mk2 buffer (this buffer contains packetBuffer)
 * @param  packetBuf    Pointer to the buffer containing packet to be sent
 * @param  size         Size of packet to be sent
 * @param  thisSideId   ID of interface associated with this thread
 * @param  otherSideId  ID of interface associated with the other thread
 */
void forwardPacket(unsigned char * mk2Buf, unsigned char * packetBuf, ssize_t size, int thisSideId, int otherSideId) {

  ssize_t sent;
#if DEBUG >= 3
  printf("[%s] Forwarding to %s\n", devs[thisSideId],devs[otherSideId] );
#endif

  /* Add MK2 header if necessary */
  if(thisSideId == ID_ETH) {
    packetBuf = mk2Buf;
    memcpy(packetBuf, &mk2TxDescriptor, sizeof(tMK2TxDescriptor));
    size += sizeof(tMK2TxDescriptor); 
  }
#if DEBUG >= 4
  dumpBuffer(packetBuf, size);
#endif

#ifdef PANAGEA2_SUPPORT
  memmove( (void*) &packetBuf[8], (const void*) packetBuf, 8);
  size -= 8;
  sent = send(sockets[otherSideId], &packetBuf[8], size, 0);
#else
  sent = send(sockets[otherSideId], packetBuf, size, 0);
 #endif
  if(sent < size) {
    if(sent < 0) {
      perror("Send failed");
      exit(1);
    }
    fprintf(stderr, "[%s] WARNING: sending incomplete packet (%d bytes out of %d)", devs[otherSideId], sent, size);
  }
}

/*
 * @desc   Receives packet on interface identified by thisSideId
 * @param  mk2Buf       Pointer to Mk2 buffer (this buffer contains packetBuffer)
 * @param  packetBuf    Pointer to the received packet 
 * @param  size         Size of Mk2 buffer, then size of the received packet
 * @param  thisSideId   ID of interface associated with this thread
 */
void receivePacket(unsigned char * mk2Buf, unsigned char ** packetBuf, ssize_t * size, int thisSideId) {

  struct msghdr msg;
  struct iovec iov[1];
  
  /* Initialize message header structure */
  memset(&msg, 0, sizeof(msg));
  memset(iov, 0, sizeof(iov));
  
#if DEBUG >= 3
  printf("Start receivePacket from %d and msg size is %d\n", thisSideId, * size );
#endif

  /* The recvmsg() call will NOT block unless a non-zero length data buffer is specified */
  if(thisSideId == ID_WAVE) {
    iov[0].iov_base = mk2Buf;
    iov[0].iov_len = *size;
#if DEBUG >= 3
  printf("Setting from ID_WAVE buffer to : %d bytes\n", *size );
#endif    
  }
  else {
    iov[0].iov_base = &mk2Buf[sizeof(tMK2TxDescriptor)];
    iov[0].iov_len = *size - sizeof(tMK2TxDescriptor);
#if DEBUG >= 3
  printf("Setting from ID_ETH buffer to : %d bytes\n", *size - sizeof(tMK2TxDescriptor) );
#endif        
  }
  msg.msg_iov = iov;
  msg.msg_iovlen = 1;

  /* Receive the packet */
  if((*size = recvmsg(sockets[thisSideId], &msg, 0)) < 0) {
    perror("Recvmsg failed");
    exit(1);
  }
  *packetBuf = iov[0].iov_base;

  /* Get rid of MK2 header and FCS if necessary */
#ifdef MK2  
  if(thisSideId == ID_WAVE) {
    *packetBuf += sizeof(tMK2RxDescriptor); 
    *size -= sizeof(tMK2RxDescriptor) + FCS_LENGTH; 
  }
#endif
  /* else { */
  /*   if(*size == 60) { */
  /*     *size = 50; */
  /*   }  */
  /*  } */

#if DEBUG >= 3
  printf("[%s] Received: %d bytes\n", devs[thisSideId], *size);
#endif
#if DEBUG >= 4
  dumpBuffer(*packetBuf, *size);
#endif

}

/*
 * @desc   Checks if a Mac address belongs to the other side
 * @param  mac          Mac address to be tested
 * @param  otherSideId  ID of interface associated with the other thread
 * @return 0 if Mac address is not from other side, >0 otherwise
 */
int isMacAddrFromOtherSide(unsigned char * mac, int otherSideId) { 

  int i, j;

  for(i=0; i < srcs_nb[otherSideId]; i++) {
    for(j=0; j < ETHER_ADDR_LEN && srcs[otherSideId][i][j] == mac[j]; j++);
    if(j >= ETHER_ADDR_LEN)
      break;
  }
  if(i < srcs_nb[otherSideId]) {
    /* loopback */
    return 1;
  }
  return 0;
}  

/*
 * @desc   Checks if a Mac address is new on this side
 * @param  mac          Mac address to be tested
 * @param  thisSideId   ID of interface associated with this thread
 * @return 0 if Mac address is not new on this side, >0 otherwise
 */
int isMacAddressNew(unsigned char * mac, int thisSideId) {
  
  int i, j;

  for(i=0; i < srcs_nb[thisSideId]; i++) {
    for(j=0; j < ETHER_ADDR_LEN && srcs[thisSideId][i][j] == mac[j]; j++);
    if(j >= ETHER_ADDR_LEN)
      break;
  }
  if(i >= srcs_nb[thisSideId]) {
#if DEBUG >= 1
    printf("[%s] New peer detected %02x:%02x:%02x:%02x:%02x:%02x\n", devs[thisSideId],
	   mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
#endif
    return 1;
  }
  return 0;
}

/*
 * @desc   Initializes a socket
 * @param  ifaceName  Interface name
 * @param  etherType  EtherType filter
 * @return Socket ID
 */
int initSocket(char * ifaceName, int etherType) {

  int s = 0;
  struct ifreq ifr;
  struct sockaddr_ll sll;
  struct packet_mreq mr;

  if((s = socket(PF_PACKET, SOCK_RAW, htons(ETH_P_ALL))) < 0) {
    perror("Unable to create socket");
    exit(1);
  }
  
  /* Retrieve interface id */
  printf( "Setting Interface name %s\n", ifaceName );
  strcpy((char *)ifr.ifr_name, ifaceName);
  if(ioctl(s, SIOCGIFINDEX, &ifr) < 0) {
    perror("Unable to retrieve interface id");
    exit(1);
  } 
    
  /* Bind socket */
  sll.sll_family = AF_PACKET;
  sll.sll_ifindex = ifr.ifr_ifindex;
  
  if ( strcmp( ifaceName, DEVICE_ETH) == 0 ) {
    sll.sll_protocol = htons(etherType);
  } else {
    sll.sll_protocol = htons(ETH_P_ALL);
  }
  
  if(bind(s, (struct sockaddr *)&sll, sizeof(sll))) {
    perror("Unable to bind socket");
    exit(1);
  }

  /* Set Promiscuous mode */
  /*
  memset(&mr, 0, sizeof(mr));
  mr.mr_ifindex = ifr.ifr_ifindex;
  mr.mr_type = PACKET_MR_PROMISC;
  if(setsockopt(s, SOL_PACKET,PACKET_ADD_MEMBERSHIP, &mr, sizeof(mr)) ) {
    perror("Unable to set PROMISCUOUS mode");
    exit(1);
  }
  */
  return s;
}

/*
 * @desc   Fills the Mk2 Tx descriptor
 * @param  tx         Pointer to Mk2 Tx Descriptor
 * @param  channel    Channel number to use for radio transmission
 * @param  qosAck     Acknoledgement mode
 * @param  mcs        Modulation and Coding scheme
 */
void prepareMk2TxDescriptor(tMK2TxDescriptor * tx, uint8_t channel, uint8_t qosAck, uint8_t mcs) {
  tx->ChannelNumber = channel;
  tx->Priority = MK2_PRIO_0;
  tx->Service = qosAck;
  tx->MCS = mcs;
  tx->TxPower.PowerSetting = MK2TPC_DEFAULT;
  tx->TxPower.ManualPower = 0;
  tx->TxAntenna = MK2_TXANT_DEFAULT;
  tx->Expiry = 0;
}

/*
 * @desc   Dumps buffer
 * @param  buf   Buffer to be dumped
 * @param  size  Size of the buffer
 */
void dumpBuffer(unsigned char * buf, int size) {

  int i;
  printf( "Dump Buffer, size %d\n" , size);
  for(i=0; i < size; i++ ) {
    printf("%02x ", buf[i]);
    if((i % 16) == 15) {
      printf("\n");
    }
  }
  if((i % 16) != 15) {
    printf("\n");
  }

  /* Flush output buffer */
  fflush(stdout);
}
