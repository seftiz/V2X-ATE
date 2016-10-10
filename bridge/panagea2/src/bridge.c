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

#include "mk2mac-api-types.h"

#define DEFAULT_ETH_TYPE 0x0707
#define DEFAULT_CHANNEL  180
#define DEFAULT_QOS      MK2_QOS_ACK
#define DEFAULT_MCS      MK2MCS_R34QPSK

extern int mk2_forward(int etherType, uint8_t channel, uint8_t qosAck, uint8_t mcs);

void usage(char * exec);

int main(int argc, char **argv) {

  int i;
  int etherType = DEFAULT_ETH_TYPE;
  uint8_t channel = DEFAULT_CHANNEL;
  uint8_t qosAck = DEFAULT_QOS;
  uint8_t mcs = DEFAULT_MCS;
  uint8_t dbg_lvl = 0;

  /* args */
  if((argc % 2) == 0) {
    fprintf(stderr, "Invalid number of parameters\n");
    usage(argv[0]);
    return(1);
  }

  /* iterate over all arguments */
  for(i=1; i < (argc - 1); i++) {
    if(strcmp("-c", argv[i]) == 0) {
      channel = atoi(argv[++i]);
      continue;
    }
    if(strcmp("-d", argv[i]) == 0) {
      dbg_lvl = atoi(argv[++i]);
      continue;
    }
    if(strcmp("-m", argv[i]) == 0) {
      mcs = atoi(argv[++i]);
      continue;
    }
    if(strcmp("-t", argv[i]) == 0) {
      etherType = atoi(argv[++i]);
      continue;
    }
    if(strcmp("-q", argv[i]) == 0) {
      char *tmp = argv[++i];
      if(strcmp(tmp, "true") == 0) {
        qosAck = MK2_QOS_ACK;
      }
      else {
        if(strcmp(tmp, "false") == 0) {
          qosAck = MK2_QOS_NOACK;
        }
        else {
          fprintf(stderr, "Invalid value for <qosAck>\n");
          usage(argv[0]);
          return(1);
        }
      }
      continue;
    }
    if((strcmp("-h", argv[i]) == 0) || (strcmp("--help", argv[i]) == 0)) {
      usage(argv[0]);
      return(0);
    }
    fprintf(stderr, "Invalid parameter %s\n", argv[i]);
    usage(argv[0]);
    return(1);
  }

  printf("[Info] Using etherType %d\n", etherType);
  printf("[Info] Using channel %d\n", channel);
  printf("[Info] Using modulation %d\n", mcs);

  return mk2_forward(etherType, channel, qosAck, mcs);
}

void usage(char * exec) {

  fprintf(stderr, "Usage:\n\t%s [-t <etherType>] [-c <channelNumber>] [-q <true|false>] [-m <modulation>]\n\n", exec);
  fprintf(stderr, "\t<etherType>\n\t\tEtherType filter (default: 0x0707) \n\n");
  fprintf(stderr, "\t<channelNumber>\n\t\tChannel number used for sending packets over the air (default: 172) \n\n");
  fprintf(stderr, "\t<qosAck> (default: true)\n");
  fprintf(stderr, "\t\ttrue\tPacket should be transmitted using normal ACK policy\n");
  fprintf(stderr, "\t\tfalse\tPacket should be transmitted without Acknoledgement\n\n");
  fprintf(stderr, "\t<modulation>\n\t\tModulation and coding scheme (default: 3/4 QPSK):\n");
  fprintf(stderr, "\t\t %2d => 1/2 BPSK\n", MK2MCS_R12BPSK);
  fprintf(stderr, "\t\t %2d => 3/4 BPSK\n", MK2MCS_R34BPSK);
  fprintf(stderr, "\t\t %2d => 1/2 QPSK\n", MK2MCS_R12QPSK);
  fprintf(stderr, "\t\t %2d => 3/4 QPSK\n", MK2MCS_R34QPSK);
  fprintf(stderr, "\t\t %2d => 1/2 16QAM\n", MK2MCS_R12QAM16);
  fprintf(stderr, "\t\t %2d => 3/4 16QAM\n", MK2MCS_R34QAM16);
  fprintf(stderr, "\t\t %2d => 2/3 64QAM\n", MK2MCS_R23QAM64);
  fprintf(stderr, "\t\t %2d => 3/4 64QAM\n\n", MK2MCS_R34QAM64);
}
