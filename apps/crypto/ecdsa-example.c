/* Copyright (C) 2014 Autotalks Ltd. */
#include <stdio.h>
#include <string.h>
#include <assert.h>
#include <inttypes.h>
#include <unistd.h>

#include "../../common/v2x_cli/v2x_cli.h"

#include <tx_api.h>

#include <atlk/sdk.h>
#include <atlk/sha.h>
#include <atlk/ecc.h>
#include <atlk/ecdsa.h>
#include <atlk/ecc_service.h>
#include <atlk/hsm_service.h>
#include <atlk/hsm_emulator.h>

#include <craton/sha_hw.h>
#include <craton/slx97_host.h>

#define HSM_PRIVATE_KEY_TYPE_PSEUDONYM 0

#if defined __CRATON_NO_ARC || defined __CRATON_ARC1

/*
  CRATON ThreadX ECDSA Example

  This example demonstrates a basic ECDSA signing/verification scenario using
  the HSM API, ECC API and CRATON SHA API for code running on top of CRATON
  processor with ThreadX RTOS.

  The device used in this example is a "HSM emulator", a term used to describe
  an emulated HSM device. The differences between an emulated HSM service
  and a real one are:
  - The emulated HSM service is created via hsm_emulator_create().
  - The implementation is not tamper-resistant because it uses general purpose
    hardware instead of tamper-resistant hardware.

  The purpose of the emulated HSM is basic software integration with
  the HSM API on a hardware platform that doesn't have a working HSM chip.
*/

/* HSM emulator service */
static hsm_service_t *example_hsm_service = NULL;

/* ECC service */
static ecc_service_t *example_ecc_service = NULL;

/* ECC socket */
static ecc_socket_t *example_ecc_socket = NULL;

/* Number of NVM cells to configure for HSM */
#define ECDSA_EXAMPLE_HSM_NVM_NUM_CELLS 128

/* ECDSA example message maximum data size in octets */
#define ECDSA_EXAMPLE_MSG_MAX_DATA_SIZE 64

/* ECDSA example message */
typedef struct {
  /* Data (octet string) */
  uint8_t data[ECDSA_EXAMPLE_MSG_MAX_DATA_SIZE];

  /* Data size in octets */
  size_t data_size;

  /* ECC elliptic curve */
  ecc_curve_t curve;

  /* ECC public key */
  ecc_point_t public_key;

  /* ECDSA fast verification signature */
  ecc_fast_verification_signature_t signature;

} ecdsa_example_message_t;

/* Format string for ECC scalar */
#define ECC_SCALAR_FMT \
  "0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx," \
  "0x%08lx,0x%08lx,0x%08lx,0x%08lx"

/* Format argument list for ecc_scalar_t */
#define ECC_SCALAR_FMT_ARGS(x)                    \
  x.value[0], x.value[1], x.value[2], x.value[3], \
  x.value[4], x.value[5], x.value[6], x.value[7], \
  x.value[8], x.value[9], x.value[10], x.value[11]

/* Format string for SHA digest */
#define SHA_256_DIGEST_FMT \
  "%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x" \
  "%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x%02x"

/* Format argument list for SHA digest */
#define SHA_256_DIGEST_FMT_ARGS(x)                      \
  x.value[0], x.value[1], x.value[2], x.value[3],       \
  x.value[4], x.value[5], x.value[6], x.value[7],       \
  x.value[8], x.value[9], x.value[10], x.value[11],     \
  x.value[12], x.value[13], x.value[14], x.value[15],   \
  x.value[16], x.value[17], x.value[18], x.value[19],   \
  x.value[20], x.value[21], x.value[22], x.value[23],   \
  x.value[24], x.value[25], x.value[26], x.value[27],   \
  x.value[28], x.value[29], x.value[30], x.value[31]

static atlk_rc_t
ecdsa_example_alice(struct cli_def *cli, ecdsa_example_message_t *msg)
{
  /* Autotalks return code */
  atlk_rc_t rc = ATLK_OK;
  /* HSM secure storage cell index */
  hsm_cell_index_t cell_index;
  /* Private key information */
  hsm_ecc_private_key_info_t private_key_info = HSM_ECC_PRIVATE_KEY_INFO_INIT;
  /* ECC point representing a public key */
  ecc_point_t public_key = ECC_POINT_INIT;
  /* SHA digest */
  sha_digest_t digest = SHA_DIGEST_INIT;
  /* ECDSA fast verification signature */
  ecc_fast_verification_signature_t signature =
    ECC_FAST_VERIFICATION_SIGNATURE_INIT;
  /* Example message */
  static const char example_msg[] =
    "Autotalks - The Confidence of Knowing Ahead";

  cli_print(cli,"\n>>> Alice\n");

  /* Print the message data */
  cli_print(cli,"Message data: %s\n", example_msg);
  cli_print(cli,"Message data size: %lu\n", (long unsigned int)sizeof(example_msg));

  /* Arbitrarily chosen HSM cell index for the sake of this example */
  cell_index = 6;
  cli_print(cli,"Using HSM cell index: %lu\n", cell_index);

  /* Using NIST P-256 elliptic curve and a pseudonym key */
  private_key_info.key_curve = ECC_CURVE_NIST_P256;
  private_key_info.key_type = HSM_PRIVATE_KEY_TYPE_PSEUDONYM;

  cli_print(cli,"Using elliptic curve ID: %u\n", private_key_info.key_curve);
  cli_print(cli,"Using key type ID: %u\n", private_key_info.key_type);

  /* Create private key and store it in the chosen cell */
  rc = hsm_ecc_private_key_create(example_hsm_service,
                                  cell_index,
                                  &private_key_info);
  if (atlk_error(rc)) {
    cli_print(cli, "hsm_ecc_private_key_create: %s\n", atlk_rc_to_str(rc));
    return rc;
  }

  cli_print(cli,"ECC private key created\n");

  /* Retrieve public key for this cell's private key */
  rc = hsm_ecc_public_key_get(example_hsm_service, cell_index, &public_key);
  if (atlk_error(rc)) {
    cli_print(cli, "hsm_ecc_public_key_get: %s\n", atlk_rc_to_str(rc));
    return rc;
  }

  assert(public_key.point_type == ECC_POINT_UNCOMPRESSED);

  /* Print retrieved ECC public key */
  cli_print(cli,"ECC public key created:\n");
  cli_print(cli,"  x: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(public_key.x_coordinate));
  cli_print(cli,"  y: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(public_key.y_coordinate));

  /* Compute SHA-256 digest of example message */
  rc = sha_hw_sha256_compute(example_msg, sizeof(example_msg), &digest);
  if (atlk_error(rc)) {
    cli_print(cli, "sha_hw_sha256_compute: %s", atlk_rc_to_str(rc));
    return rc;
  }

  /* Print computed SHA-256 digest */
  cli_print(cli,"SHA-256 hash digest computed:\n");
  cli_print(cli,"  Digest: " SHA_256_DIGEST_FMT "\n", SHA_256_DIGEST_FMT_ARGS(digest));

  /* Generate ECDSA fast verification signature */
  rc = hsm_ecdsa_sign(example_hsm_service, cell_index, &digest, &signature);
  if (atlk_error(rc)) {
    cli_print(cli, "hsm_ecdsa_sign: %s\n", atlk_rc_to_str(rc));
    return rc;
  }

  assert(signature.R_point.point_type == ECC_POINT_UNCOMPRESSED);

  /* Print generated ECDSA signature */
  cli_print(cli,"ECDSA signature generated:\n");
  cli_print(cli,"  Rx: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(signature.R_point.x_coordinate));
  cli_print(cli,"  Ry: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(signature.R_point.y_coordinate));
  cli_print(cli,"  s: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(signature.s_scalar));

  /* Make sure the example message can fit into the data */
  assert(sizeof(example_msg) <= sizeof(msg->data));

  /* Produce the message */
  msg->data_size = sizeof(example_msg);
  memcpy(msg->data, example_msg, msg->data_size);
  msg->curve = private_key_info.key_curve;
  msg->public_key = public_key;
  msg->signature = signature;

  return ATLK_OK;
}

static atlk_rc_t
ecdsa_example_bob( struct cli_def *cli, const ecdsa_example_message_t *msg)
{
  /* Autotalks return code */
  atlk_rc_t rc = ATLK_OK;
  /* SHA digest */
  sha_digest_t digest = SHA_DIGEST_INIT;
  /* ECDSA signature */
  ecc_signature_t signature = ECC_SIGNATURE_INIT;
  /* ECC request */
  ecc_request_t request = ECC_REQUEST_INIT;
  /* ECC response */
  ecc_response_t response = ECC_RESPONSE_INIT;
  /* ECC request identifier */
  ecc_request_id_t request_id;

  cli_print(cli,"\n>>> Bob\n");

  /* Print received message */
  cli_print(cli,"Message data: %s\n", msg->data);
  cli_print(cli,"Message data size: %lu\n", (long unsigned int)msg->data_size);
  cli_print(cli,"Using elliptic curve ID: %u\n", msg->curve);

  assert(msg->public_key.point_type == ECC_POINT_UNCOMPRESSED);

  /* Print received ECC public key */
  cli_print(cli,"ECC public key:\n");
  cli_print(cli,"  x: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(msg->public_key.x_coordinate));
  cli_print(cli,"  y: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(msg->public_key.y_coordinate));

  /* Print received ECDSA signature for fast verification */
  cli_print(cli,"ECDSA signature:\n");
  cli_print(cli,"  Rx: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(msg->signature.R_point.x_coordinate));
  cli_print(cli,"  Ry: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(msg->signature.R_point.y_coordinate));
  cli_print(cli,"  s: " ECC_SCALAR_FMT "\n",
    ECC_SCALAR_FMT_ARGS(msg->signature.s_scalar));

  /* Compute SHA-256 hash value of received message */
  rc = sha_hw_sha256_compute(msg->data, msg->data_size, &digest);
  if (atlk_error(rc)) {
    cli_print(cli, "sha_hw_sha256_compute: %s", atlk_rc_to_str(rc));
    return rc;
  }

  /* Print computed SHA-256 digest */
  cli_print(cli,"SHA-256 hash digest computed:\n");
  cli_print(cli,"  Digest: " SHA_256_DIGEST_FMT "\n", SHA_256_DIGEST_FMT_ARGS(digest));

  /* Convert ECDSA signature for fast verification */
  rc = ecdsa_signature_convert(msg->curve, &msg->signature, &signature);
  if (atlk_error(rc)) {
    cli_print(cli, "ecdsa_signature_convert: %s", atlk_rc_to_str(rc));
    return rc;
  }

  /* Print converted ECDSA signature for fast verification */
  cli_print(cli,"Converted ECDSA signature for fast verification:\n");
  cli_print(cli,"  r: " ECC_SCALAR_FMT "\n", ECC_SCALAR_FMT_ARGS(signature.r_scalar));
  cli_print(cli,"  s: " ECC_SCALAR_FMT "\n", ECC_SCALAR_FMT_ARGS(signature.s_scalar));

  /* Arbitrary request identifier */
  request_id = 10;

  /* Fill ECC request */
  request.context.request_id = request_id;
  request.context.request_type = ECC_REQUEST_TYPE_VERIFY;
  request.context.curve = msg->curve;
  request.params.verify_params.public_key = msg->public_key;
  request.params.verify_params.digest = digest;
  request.params.verify_params.signature = signature;

  /* Send ECC request */
  rc = ecc_request_send(example_ecc_socket, &request, NULL);
  if (atlk_error(rc)) {
    cli_print(cli, "ecc_verification_request_send: %s\n", atlk_rc_to_str(rc));
    return rc;
  }

  /* Print ECC verification request ID */
  cli_print(cli,"Sent ECC request with ID %" PRIu32 "\n", request_id);

  /* Receive ECC response */
  rc = ecc_response_receive(example_ecc_socket, &response, &atlk_wait_forever);
  if (atlk_error(rc)) {
      cli_print(cli, "ecc_verification_response_receive: %s\n",
      atlk_rc_to_str(rc));
    return rc;
  }

  /* Print ECC verification response */
  cli_print(cli,"ECC response for request ID %" PRIu32 ": %d\n",
    response.context.request_id, response.rc);

  /* Print ECC verification response result */
  if (response.rc == ECC_OK) {
    cli_print(cli,"SUCCESS\n");
  }
  else {
    cli_print(cli,"FAILURE\n");
  }

  return rc;
}


int
cli_ecdsa_example( struct cli_def *cli, const char *command, char *argv[], int argc )
{
  /* Autotalks return code */
  atlk_rc_t rc = ATLK_OK;
  /* ECDSA example message */
  ecdsa_example_message_t message;
  /* HSM capability information */
  hsm_capability_info_t hsm_capability_info = HSM_CAPABILITY_INFO_INIT;
  /* HSM NVM configuration */
  hsm_nvm_config_t hsm_nvm_config = HSM_NVM_CONFIG_INIT;

  (void) command;
  (void) argv;
  (void) argc;

  IS_HELP_ARG("apps crypto ecdsa start")


  /* Create HSM emulator service */
  // rc = hsm_emulator_create(NULL, &example_hsm_service);
	rc = slx97_host_hsm_service_get(&example_hsm_service);
  if (atlk_error(rc)) {
    cli_print(cli, "hsm_emulator_create: %s\n", atlk_rc_to_str(rc));
    goto out;
  }

  /* Get HSM capability information */
  rc = hsm_capability_info_get(example_hsm_service, &hsm_capability_info);
  if (atlk_error(rc)) {
    cli_print(cli, "hsm_capability_info_get: %s", atlk_rc_to_str(rc));
    goto out;
  }

  cli_print(cli,"HSM capability information:\n");
  cli_print(cli,"  Maximum number of NVM cells: %lu\n",
    hsm_capability_info.max_num_of_cells);
  cli_print(cli,"  Current number of NVM cells: %lu\n",
    hsm_capability_info.current_num_of_cells);
  cli_print(cli,"  Maximum number of cell ranges supported by "
         "hsm_csr_ecdsa_public_keys_sign(): %lu\n",
    hsm_capability_info.max_num_of_cell_ranges_for_csr);

  cli_print(cli,"Initializing NVM to contain %u cells\n",
    ECDSA_EXAMPLE_HSM_NVM_NUM_CELLS);

  hsm_nvm_config.num_of_cells = ECDSA_EXAMPLE_HSM_NVM_NUM_CELLS;

  /* Initialize HSM NVM */
  rc = hsm_nvm_init(example_hsm_service, &hsm_nvm_config);
  if (atlk_error(rc)) {
    cli_print(cli, "hsm_nvm_init: %s", atlk_rc_to_str(rc));
    goto out;
  }

  /* Get default ECC service */
  rc = ecc_default_service_get(&example_ecc_service);
  if (atlk_error(rc)) {
    cli_print(cli,"ecc_default_service_get: %s\n", atlk_rc_to_str(rc));
    goto out;
  }

  /* Create ECC verification socket */
  rc = ecc_socket_create(example_ecc_service, &example_ecc_socket);
  if (atlk_error(rc)) {
    cli_print(cli, "ecc_verification_socket_create: %s\n", atlk_rc_to_str(rc));
    goto out;
  }

  /* Produce example message by Alice */
  rc = ecdsa_example_alice(cli, &message);
  if (atlk_error(rc)) {
    goto out;
  }

  /* Consume example message by Bob */
  rc = ecdsa_example_bob(cli, &message);
  if (atlk_error(rc)) {
    goto out;
  }

out:
  if (atlk_error(rc)) {
    cli_print(cli, "ERROR\n");
  }

  /* Delete ECC verification socket */
  ecc_socket_delete(example_ecc_socket);
  example_ecc_socket = NULL;

  /* Delete ECC service */
  ecc_service_delete(example_ecc_service);
  example_ecc_service = NULL;

  /* Delete HSM emulator service */
  hsm_service_delete(example_hsm_service);
  example_hsm_service = NULL;

  return CLI_OK;
}

#else /* __CRATON_NO_ARC || __CRATON_ARC1 */

int
cli_ecdsa_example( struct cli_def *cli, const char *command, char *argv[], int argc )
{
  cli_print(cli, "NOT SUPPORTTED IN MC");
}
#endif /* __CRATON_NO_ARC || __CRATON_ARC1 */
